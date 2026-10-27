using TheLivingCanvas.Core;
using UnityEngine;

namespace TheLivingCanvas.Audio
{
    /// <summary>
    /// Música de fondo: reproduce las piezas en orden aleatorio (sin repetir la misma dos veces seguidas) y las funde
    /// entre sí: la siguiente empieza mientras la actual termina. Usa tiempo sin escala (suena con la pausa abierta)
    /// y respeta el volumen de música de los ajustes.
    /// </summary>
    public class MusicPlaylist : MonoBehaviour
    {
        [SerializeField] AudioClip[] tracks;
        [SerializeField, Range(0f, 1f)] float volume = 0.5f;
        [SerializeField] float crossfadeSeconds = 6f;
        [SerializeField] float fadeInSeconds = 2f;

        AudioSource current, next;
        int currentIndex = -1;
        float fadeIn;
        bool crossfading;
        float crossfadeT;

        void Awake()
        {
            current = CreateSource();
            next = CreateSource();
        }

        void Start()
        {
            if (tracks == null || tracks.Length == 0) { enabled = false; return; }
            Begin(current, PickNext());
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            fadeIn = Mathf.Min(1f, fadeIn + dt / Mathf.Max(0.01f, fadeInSeconds));
            float level = volume * fadeIn * GameSettings.MusicVolume;

            if (!crossfading)
            {
                current.volume = level;
                // Con la pieza a punto de acabar, empieza la siguiente.
                if (current.clip != null && current.clip.length - current.time <= crossfadeSeconds && current.isPlaying)
                {
                    Begin(next, PickNext());
                    crossfading = true;
                    crossfadeT = 0f;
                }
                else if (!current.isPlaying && current.clip != null && current.time == 0f)
                {
                    Begin(current, PickNext()); // la pieza ya acabó (p. ej. la pausa de la aplicación la cortó)
                }
                return;
            }

            crossfadeT += dt / Mathf.Max(0.01f, crossfadeSeconds);
            current.volume = level * (1f - crossfadeT);
            next.volume = level * crossfadeT;
            if (crossfadeT >= 1f)
            {
                current.Stop();
                (current, next) = (next, current);
                crossfading = false;
            }
        }

        AudioSource CreateSource()
        {
            var s = gameObject.AddComponent<AudioSource>();
            s.loop = false;
            s.playOnAwake = false;
            s.spatialBlend = 0f;
            s.ignoreListenerPause = true;
            return s;
        }

        void Begin(AudioSource source, int index)
        {
            currentIndex = index;
            source.clip = tracks[index];
            source.volume = 0f;
            source.Play();
        }

        int PickNext()
        {
            if (tracks.Length == 1) return 0;
            int i;
            do i = Random.Range(0, tracks.Length); while (i == currentIndex);
            return i;
        }
    }
}
