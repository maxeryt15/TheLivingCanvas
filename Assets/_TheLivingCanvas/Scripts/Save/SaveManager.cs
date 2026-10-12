using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Progression;
using UnityEngine;

namespace TheLivingCanvas.Save
{
    /// <summary>
    /// Guardado único con autoguardado: al salir, cada 60 s y poco después de cambios importantes
    /// (monedas, nivel, inventario). Carga sola al empezar, tras todos los Awake y antes de los demás Start.
    /// </summary>
    [DefaultExecutionOrder(-50)]
    public class SaveManager : MonoBehaviour
    {
        [SerializeField] Wallet wallet;
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] PlayerInventory inventory;
        [SerializeField] SaveRegistry registry = new();
        [SerializeField] float autosaveSeconds = 60f;
        [Tooltip("Espera tras un cambio importante antes de guardar (agrupa ráfagas de cambios).")]
        [SerializeField] float debounceSeconds = 2f;

        List<ISaveable> saveables;
        bool loading;
        bool dirty;
        float dirtyTime;
        float nextAutosave;

        /// <summary>Ruta de la partida guardada.</summary>
        public static string SavePath => Path.Combine(Application.persistentDataPath, "save", "save.json");

        void OnEnable()
        {
            wallet.Changed += OnWalletChanged;
            artistLevel.Changed += MarkDirty;
            inventory.Changed += MarkDirty;
        }

        void OnDisable()
        {
            wallet.Changed -= OnWalletChanged;
            artistLevel.Changed -= MarkDirty;
            inventory.Changed -= MarkDirty;
        }

        void Start()
        {
            Load();
            nextAutosave = Time.unscaledTime + autosaveSeconds;
        }

        void Update()
        {
            float now = Time.unscaledTime;
            if (now >= nextAutosave || (dirty && now >= dirtyTime)) Save();
        }

        void OnApplicationQuit() => Save();

        void OnWalletChanged(int total, int delta) => MarkDirty();

        void MarkDirty()
        {
            if (loading || dirty) return;
            dirty = true;
            dirtyTime = Time.unscaledTime + debounceSeconds;
        }

        List<ISaveable> FindSaveables() =>
            FindObjectsByType<MonoBehaviour>(FindObjectsInactive.Include, FindObjectsSortMode.None).OfType<ISaveable>().ToList();

        void Load()
        {
            saveables = FindSaveables();
            string path = SavePath;
            if (!File.Exists(path)) return; // partida nueva: valen los valores de la escena

            SaveData data;
            try
            {
                data = JsonUtility.FromJson<SaveData>(File.ReadAllText(path));
                if (data == null || data.version < 1 || data.version > SaveData.CurrentVersion)
                    throw new InvalidDataException($"unsupported save version {data?.version}");
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[Save] Could not read {path} ({e.Message}); starting a new game and keeping the old file as save.json.bad.");
                BackupCorrupt(path);
                return;
            }

            loading = true; // los eventos que dispara la carga no son cambios por guardar
            foreach (var saveable in saveables)
            {
                try { saveable.ReadSave(data, registry); }
                catch (Exception e) { Debug.LogException(e); }
            }
            loading = false;
        }

        static void BackupCorrupt(string path)
        {
            try
            {
                string bad = path + ".bad";
                if (File.Exists(bad)) File.Delete(bad);
                File.Move(path, bad);
            }
            catch (Exception e) { Debug.LogException(e); }
        }

        /// <summary>Escribe la partida (a un archivo temporal que luego sustituye al anterior, para no dejarla a medias).</summary>
        public void Save()
        {
            dirty = false;
            nextAutosave = Time.unscaledTime + autosaveSeconds;
            saveables ??= FindSaveables();

            var data = new SaveData();
            foreach (var saveable in saveables)
                if (saveable != null) saveable.WriteSave(data);

            try
            {
                string path = SavePath;
                string temp = path + ".tmp";
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllText(temp, JsonUtility.ToJson(data, true));
                if (File.Exists(path)) File.Replace(temp, path, null);
                else File.Move(temp, path);
            }
            catch (Exception e) { Debug.LogException(e); }
        }

        /// <summary>Borra la partida guardada (para probar, con el juego parado; el botón de partida nueva llega en la 18D).</summary>
        [ContextMenu("Delete Save")]
        void DeleteSave()
        {
            if (File.Exists(SavePath)) File.Delete(SavePath);
        }
    }
}
