using System;
using UnityEngine;

namespace TheLivingCanvas.Ui
{
    /// <summary>Estado en que se encuentra la pantalla de carga; decide qué mensaje se muestra.</summary>
    public enum LoadingState { Idle, Preparing, Loading, Activating, Completing, Revealing, Failed }

    /// <summary>
    /// Configuración artística de la pantalla de carga (Resources/LoadingScreenSettings.asset): variantes de ilustración,
    /// mensajes, tiempos y accesibilidad. La lógica de carga (SceneLoader) no contiene valores de arte.
    /// Si el asset falta se usan estos mismos valores por defecto.
    /// </summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Loading Screen Settings", fileName = "LoadingScreenSettings")]
    public class LoadingScreenSettings : ScriptableObject
    {
        /// <summary>Una ilustración: el mismo paisaje a lápiz (boceto) y pintado. El progreso va pintando el boceto.</summary>
        [Serializable]
        public class Variant
        {
            public string name = "Garden";
            [Tooltip("Papel envejecido de fondo (si falta, color liso).")] public Sprite paper;
            [Tooltip("Boceto a carbón del paisaje.")] public Sprite sketch;
            [Tooltip("El paisaje pintado; se descubre con el progreso.")] public Sprite painted;
            [Tooltip("Variante apagada (azul grisáceo) con la flor amarilla intacta: solo se usa si 'Use Faded' está activo y la Descoloración ya ocurrió.")]
            public Sprite paintedFaded;
            [Tooltip("Tinte del papel.")] public Color paperTint = new Color(.93f, .87f, .74f, 1f);
        }

        [Serializable]
        public class MessageSet
        {
            public LoadingState state;
            public string[] messages;
        }

        [Header("Artwork")]
        public Variant[] variants;
        [Tooltip("Mostrar la versión apagada de la ilustración. Es manual a propósito: no debe adelantar el progreso de la historia.")]
        public bool useFaded;
        [Tooltip("Mostrar el título del juego bajo la ilustración.")] public bool showTitle = true;
        public string title = "The Living Canvas";

        [Header("Timing (seconds)")]
        [Min(0f)] public float coverSeconds = 0.9f;
        [Min(0f)] public float entryFade = 0.4f;
        [Tooltip("Duración mínima visible del contenido.")]
        [Min(0f)] public float minDisplay = 1.6f;
        [Tooltip("Segundos que se prolonga la pantalla DESPUÉS de cargar (la escena ya está lista pero sin activar), para que la pintura se vea avanzar. 0 = sin espera.")]
        [Min(0f)] public float postLoadSeconds = 5f;
        [Tooltip("Cuánto tarda la pincelada del progreso en alcanzar el valor real (menor = más suave).")]
        [Min(0.01f)] public float progressSmoothing = 0.35f;
        [Min(0f)] public float completionHold = 0.35f;
        [Min(0f)] public float exitFade = 0.4f;
        [Min(0f)] public float uncoverSeconds = 0.9f;
        [Tooltip("Si la carga no avanza durante este tiempo se aborta y se vuelve a la escena anterior.")]
        [Min(5f)] public float timeoutSeconds = 60f;

        [Header("Motion")]
        [Range(0f, 1f)] public float ambientIntensity = 0.5f;
        public AnimationCurve revealCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);

        [Header("Text")]
        [Tooltip("Segundos entre mensajes del mismo estado.")] [Min(2f)] public float messageInterval = 5f;
        public MessageSet[] messages = DefaultMessages();

        [Header("Diagnostics")]
        public bool debugLog;

        static LoadingScreenSettings current;

        public static LoadingScreenSettings Current
        {
            get
            {
                if (current == null) current = Resources.Load<LoadingScreenSettings>("LoadingScreenSettings");
                if (current == null) { current = CreateInstance<LoadingScreenSettings>(); current.hideFlags = HideFlags.DontSave; }
                return current;
            }
        }

        public string RandomMessage(LoadingState state, string last = null)
        {
            if (messages != null)
                foreach (var set in messages)
                {
                    if (set == null || set.state != state || set.messages == null || set.messages.Length == 0) continue;
                    if (set.messages.Length == 1) return set.messages[0];
                    string pick;
                    int guard = 0;
                    do pick = set.messages[UnityEngine.Random.Range(0, set.messages.Length)]; while (pick == last && ++guard < 8);
                    return pick;
                }
            return "";
        }

        static MessageSet[] DefaultMessages() => new[]
        {
            new MessageSet { state = LoadingState.Preparing, messages = new[] { "Preparing the colors…", "Arranging the canvas…", "Setting up the easel…" } },
            new MessageSet { state = LoadingState.Loading, messages = new[] { "Preparing the gallery…", "Every painting begins somewhere…", "Finding a little more color…", "Taking a moment to look closer…", "Letting the light settle…", "Some rooms take their time…" } },
            new MessageSet { state = LoadingState.Activating, messages = new[] { "Opening the doors…" } },
            new MessageSet { state = LoadingState.Completing, messages = new[] { "Ready." } },
            new MessageSet { state = LoadingState.Failed, messages = new[] { "We couldn't open that room. Returning to where you were." } },
        };
    }
}
