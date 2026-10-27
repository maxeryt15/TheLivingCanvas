using TheLivingCanvas.Seasons;
using UnityEngine;

namespace TheLivingCanvas.Audio
{
    /// <summary>
    /// Música de fondo: dos pistas en bucle, una de día (6:00–18:00) y otra de tarde-noche, que se funden
    /// al cruzar las 18:00. Usa tiempo sin escala: sigue sonando con el menú de pausa abierto.
    /// </summary>
    public class MusicPlayer : MonoBehaviour
    {
        const float EveningStartMinutes = 720f; // 18:00, contando desde las 6:00

        [SerializeField] SeasonClock seasons;
        [SerializeField] AudioClip dayTrack;
        [SerializeField] AudioClip eveningTrack;
        [SerializeField, Range(0f, 1f)] float volume = 0.5f;
        [SerializeField] float crossfadeSeconds = 6f;
        [SerializeField] float fadeInSeconds = 2f;

        AudioSource day;
        AudioSource evening;
        float eveningMix; // 0 = solo día, 1 = solo tarde
        float masterFade; // 0..1: entrada suave al empezar

        void Awake()
        {
            day = CreateSource(dayTrack);
            evening = CreateSource(eveningTrack);
        }

        // En Start: la partida (SaveManager, que va antes) ya restauró la hora, así empieza con la pista que toca.
        void Start()
        {
            eveningMix = IsEvening ? 1f : 0f;
            ApplyVolumes();
            day.Play();
            evening.Play();
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            masterFade = Mathf.Min(1f, masterFade + dt / Mathf.Max(0.01f, fadeInSeconds));
            eveningMix = Mathf.MoveTowards(eveningMix, IsEvening ? 1f : 0f, dt / Mathf.Max(0.01f, crossfadeSeconds));
            ApplyVolumes();
        }

        bool IsEvening => seasons.MinutesOfDay >= EveningStartMinutes;

        AudioSource CreateSource(AudioClip clip)
        {
            var source = gameObject.AddComponent<AudioSource>();
            source.clip = clip;
            source.loop = true;
            source.playOnAwake = false;
            source.spatialBlend = 0f;
            source.ignoreListenerPause = true;
            return source;
        }

        void ApplyVolumes()
        {
            float level = volume * masterFade * Core.GameSettings.MusicVolume;
            day.volume = level * (1f - eveningMix);
            evening.volume = level * eveningMix;
        }
    }
}
