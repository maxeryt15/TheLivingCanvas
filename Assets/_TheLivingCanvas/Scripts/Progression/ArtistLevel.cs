using System;
using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Data;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Save;
using UnityEngine;

namespace TheLivingCanvas.Progression
{
    /// <summary>Lo que dio una pintura terminada: XP total y qué lo motivó.</summary>
    public readonly struct XpGain
    {
        public readonly int Xp;
        public readonly bool NewCrop;
        public readonly bool NewVariant;
        public readonly bool LeveledUp;

        public XpGain(int xp, bool newCrop, bool newVariant, bool leveledUp)
        {
            Xp = xp;
            NewCrop = newCrop;
            NewVariant = newVariant;
            LeveledUp = leveledUp;
        }
    }

    /// <summary>Nivel de artista del jugador: se gana XP al terminar pinturas.</summary>
    public class ArtistLevel : MonoBehaviour, ISaveable
    {
        [Tooltip("XP acumulada necesaria para cada nivel (el primero es el nivel 1).")]
        [SerializeField] int[] levelThresholds = { 0, 60, 150, 300, 500, 750 };
        [Tooltip("XP por pintura terminada, en el orden de PaintingQuality.")]
        [SerializeField] int[] xpPerQuality = { 10, 20, 35, 50 };
        [SerializeField] int discoveryBonus = 25;

        // Claves "cultivo" y "cultivo:variante" ya pintados, para dar el bono de descubrimiento una sola vez.
        readonly HashSet<string> discovered = new();
        // Ids de los sets de la colección ya reclamados.
        readonly HashSet<string> claimedSets = new();
        int xp;

        public int Xp => xp;
        public int MaxLevel => levelThresholds.Length;
        public bool IsMaxLevel => Level >= MaxLevel;

        public int Level
        {
            get
            {
                int level = 1;
                while (level < MaxLevel && xp >= levelThresholds[level]) level++;
                return level;
            }
        }

        /// <summary>XP acumulada que pide el siguiente nivel (sin sentido en el nivel máximo).</summary>
        public int NextLevelXp => levelThresholds[Level];

        /// <summary>Avance dentro del nivel actual (0–1); 1 en el nivel máximo.</summary>
        public float Progress
        {
            get
            {
                if (IsMaxLevel) return 1f;
                int start = levelThresholds[Level - 1];
                return (xp - start) / (float)(NextLevelXp - start);
            }
        }

        /// <summary>Cambió la XP (y quizá el nivel).</summary>
        public event Action Changed;

        /// <summary>Se subió de nivel: nivel nuevo.</summary>
        public event Action<int> LeveledUp;

        /// <summary>Si ya se pintó el cultivo (o la variante) alguna vez: lo usa la colección de la galería.</summary>
        public bool IsDiscovered(CropDefinition crop) => discovered.Contains(crop.Id);

        public bool IsDiscovered(CropDefinition crop, CropVariant variant) => discovered.Contains(Key(crop, variant));

        static string Key(CropDefinition crop, CropVariant variant) => $"{crop.Id}:{variant.id}";

        /// <summary>Si ya se cosechó una planta con esa mutación.</summary>
        public bool IsDiscovered(Mutation mutation) => discovered.Contains(Key(mutation));

        static string Key(Mutation mutation) => $"mutation:{mutation.ToString().ToLowerInvariant()}";

        /// <summary>Registra la mutación al cosecharla; true si era la primera vez.</summary>
        public bool DiscoverMutation(Mutation mutation)
        {
            if (!discovered.Add(Key(mutation))) return false;
            Changed?.Invoke();
            return true;
        }

        public bool IsClaimed(CollectionSet set) => claimedSets.Contains(set.Id);

        /// <summary>Marca el set como reclamado; false si ya lo estaba.</summary>
        public bool Claim(CollectionSet set)
        {
            if (!claimedSets.Add(set.Id)) return false;
            Changed?.Invoke();
            return true;
        }

        /// <summary>Da la XP de una pintura terminada; la variante puede ser null si no salió ninguna.</summary>
        public XpGain AwardPainting(PaintingQuality quality, CropDefinition crop, CropVariant variant)
        {
            int gained = xpPerQuality[(int)quality];
            bool newCrop = discovered.Add(crop.Id);
            bool newVariant = variant != null && discovered.Add(Key(crop, variant));
            if (newCrop) gained += discoveryBonus;
            if (newVariant) gained += discoveryBonus;

            return new XpGain(gained, newCrop, newVariant, AddXp(gained));
        }

        /// <summary>Suma XP directa (ej. recompensa de un encargo); devuelve si subió de nivel.</summary>
        public bool AddXp(int amount)
        {
            int levelBefore = Level;
            xp += amount;
            Changed?.Invoke();
            bool leveledUp = Level > levelBefore;
            if (leveledUp) LeveledUp?.Invoke(Level);
            return leveledUp;
        }

        public void WriteSave(SaveData data)
        {
            data.xp = xp;
            data.discovered = discovered.ToList();
            data.claimedSets = claimedSets.ToList();
        }

        /// <summary>Restaura sin disparar LeveledUp: la puerta del jardín y la tienda leen el nivel al empezar.</summary>
        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            xp = Mathf.Max(0, data.xp);
            discovered.Clear();
            discovered.UnionWith(data.discovered);
            claimedSets.Clear();
            foreach (var id in data.claimedSets)
                if (registry.FindSet(id) != null) claimedSets.Add(id);
            Changed?.Invoke();
        }
    }
}
