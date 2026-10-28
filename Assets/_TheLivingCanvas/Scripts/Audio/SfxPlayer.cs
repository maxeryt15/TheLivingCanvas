using TheLivingCanvas.Economy;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Progression;
using UnityEngine;

namespace TheLivingCanvas.Audio
{
    /// <summary>Efectos de sonido disponibles para <see cref="SfxPlayer.Play"/>.</summary>
    public enum Sfx { PaintFinish, Harvest, Coin, UiOpen, UiClose, Place, LevelUp }

    /// <summary>
    /// Efectos de sonido 2D. Los eventos que ya existen (monedas, nivel, cosecha) se escuchan aquí; el resto
    /// lo pide quien lo provoca con la API estática, que no hace nada si no hay SfxPlayer en la escena.
    /// </summary>
    public class SfxPlayer : MonoBehaviour
    {
        const float PitchVariation = 0.05f;

        [SerializeField] Wallet wallet;
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] PlayerInventory inventory;
        [SerializeField, Range(0f, 1f)] float volume = 0.8f;
        [SerializeField] AudioClip brushLoop;
        [SerializeField] AudioClip paintFinish;
        [SerializeField] AudioClip harvest;
        [SerializeField] AudioClip coin;
        [SerializeField] AudioClip uiOpen;
        [SerializeField] AudioClip uiClose;
        [SerializeField] AudioClip place;
        [SerializeField] AudioClip levelUp;

        static SfxPlayer instance;

        AudioSource oneShots;
        AudioSource brush;

        void Awake()
        {
            instance = this;
            oneShots = CreateSource(null, false);
            brush = CreateSource(brushLoop, true);
        }

        void Update()
        {
            float level = volume * Core.GameSettings.SfxVolume;
            oneShots.volume = level;
            brush.volume = level;
        }

        void OnEnable()
        {
            wallet.Changed += OnCoinsChanged;
            artistLevel.LeveledUp += OnLeveledUp;
            inventory.ItemAdded += OnItemAdded;
        }

        void OnDisable()
        {
            wallet.Changed -= OnCoinsChanged;
            artistLevel.LeveledUp -= OnLeveledUp;
            inventory.ItemAdded -= OnItemAdded;
        }

        void OnDestroy()
        {
            if (instance == this) instance = null;
        }

        /// <summary>Suena el efecto una vez, con un poco de variación de tono.</summary>
        public static void Play(Sfx id)
        {
            if (instance != null) instance.PlayOneShot(id);
        }

        /// <summary>Enciende o apaga el sonido continuo del pincel.</summary>
        public static void SetBrushing(bool active)
        {
            if (instance == null || instance.brush.isPlaying == active) return;
            if (active) instance.brush.Play();
            else instance.brush.Stop();
        }

        AudioSource CreateSource(AudioClip clip, bool loop)
        {
            var source = gameObject.AddComponent<AudioSource>();
            source.clip = clip;
            source.loop = loop;
            source.playOnAwake = false;
            source.spatialBlend = 0f;
            source.volume = volume;
            return source;
        }

        void PlayOneShot(Sfx id)
        {
            var clip = id switch
            {
                Sfx.PaintFinish => paintFinish,
                Sfx.Harvest => harvest,
                Sfx.Coin => coin,
                Sfx.UiOpen => uiOpen,
                Sfx.UiClose => uiClose,
                Sfx.Place => place,
                _ => levelUp
            };
            if (clip == null) return;
            oneShots.pitch = 1f + Random.Range(-PitchVariation, PitchVariation);
            oneShots.PlayOneShot(clip);
        }

        void OnCoinsChanged(int total, int delta)
        {
            if (delta > 0) Play(Sfx.Coin);
        }

        void OnLeveledUp(int level) => Play(Sfx.LevelUp);

        void OnItemAdded(InventoryItem item)
        {
            if (item is CropItem) Play(Sfx.Harvest);
        }
    }
}
