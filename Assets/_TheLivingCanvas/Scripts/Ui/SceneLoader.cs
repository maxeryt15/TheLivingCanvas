using System.Collections;
using TheLivingCanvas.Core;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Controlador de carga de escenas. Solo contiene la lógica (estados, progreso honesto, errores); el arte y los tiempos
    /// viven en LoadingScreenSettings y la presentación en LoadingScreenView. Se crea solo la primera vez y sobrevive a
    /// los cambios de escena. Uso: SceneLoader.Load("Museum").
    ///
    /// Progreso mostrado: la carga real ocupa el 0–40 % de la barra (op.progress, que Unity detiene en 0,9 hasta activar);
    /// después hay una espera de presentación (postLoadSeconds, 5 s por defecto) en la que la barra y la pintura avanzan
    /// linealmente hasta el 95 % con la escena ya cargada pero sin activar; el 100 % solo cuando la escena nueva ya está
    /// activa y asentada. La barra suaviza hacia el valor y nunca retrocede.
    /// </summary>
    public class SceneLoader : MonoBehaviour
    {
        public const string MenuScene = "MainMenu";
        public const string GameScene = "Museum";

        const float LoadShare = 0.4f, ActivateShare = 0.95f;

        static SceneLoader instance;
        static int lastVariant = -1;

        LoadingScreenView view;
        LoadingScreenSettings cfg;
        bool loading;
        LoadingState state = LoadingState.Idle;
        float shown; // progreso visible, monótono

        public static bool IsLoading => instance != null && instance.loading;
        public static LoadingState State => instance != null ? instance.state : LoadingState.Idle;

        public static void Load(string sceneName)
        {
            if (!InBuild(sceneName))
            {
                Debug.LogError($"SceneLoader: la escena '{sceneName}' no existe o no está en Build Settings.");
                return;
            }
            if (instance == null)
            {
                var go = new GameObject("SceneLoader");
                DontDestroyOnLoad(go);
                instance = go.AddComponent<SceneLoader>();
            }
            if (instance.loading) { instance.Log("Carga ya en curso: petición ignorada."); return; }
            instance.StartCoroutine(instance.Run(sceneName));
        }

        static bool InBuild(string sceneName)
        {
            if (string.IsNullOrEmpty(sceneName)) return false;
            for (int i = 0; i < SceneManager.sceneCountInBuildSettings; i++)
                if (System.IO.Path.GetFileNameWithoutExtension(SceneUtility.GetScenePathByBuildIndex(i)) == sceneName) return true;
            return false;
        }

        void EnsureView()
        {
            cfg = LoadingScreenSettings.Current;
            if (view == null) view = LoadingScreenView.Create(transform);
        }

        void Log(string msg) { if (cfg != null && cfg.debugLog) Debug.Log("SceneLoader: " + msg); }

        void SetState(LoadingState s)
        {
            state = s;
            Log("estado → " + s);
        }

        IEnumerator Run(string sceneName)
        {
            EnsureView();
            loading = true;
            shown = 0f;
            bool ok = false;
            try
            {
                // 1. Preparar: elegir ilustración, cubrir la pantalla con papel y mostrar el lienzo
                SetState(LoadingState.Preparing);
                var variant = PickVariant();
                view.SetVariant(variant, cfg.useFaded, cfg.title, cfg.showTitle);
                view.ApplyContrast(GameSettings.HighContrastText);
                string message = cfg.RandomMessage(LoadingState.Preparing);
                view.SetMessage(message, true);
                view.BlocksRaycasts = true;
                UIEvents.Play(UISound.LoadingStart);
                yield return ScreenTransition.Cover(ScreenTransition.Kind.Brush, view.PaperColor, cfg.coverSeconds);
                yield return FadeView(1f, cfg.entryFade);

                // 2. Cargar de verdad (sin activar) y mostrar el progreso real
                SetState(LoadingState.Loading);
                message = cfg.RandomMessage(LoadingState.Loading, message);
                view.SetMessage(message);
                float started = Time.unscaledTime, lastAdvance = started, lastReal = 0f, nextMessage = started + cfg.messageInterval;
                var op = SceneManager.LoadSceneAsync(sceneName);
                if (op == null) { yield return Fail($"LoadSceneAsync('{sceneName}') devolvió null."); yield break; }
                op.allowSceneActivation = false;

                while (op.progress < 0.9f)
                {
                    float real = Mathf.Clamp01(op.progress / 0.9f);
                    if (real > lastReal + 0.001f) { lastReal = real; lastAdvance = Time.unscaledTime; }
                    else if (op.progress < 0.9f && Time.unscaledTime - lastAdvance > cfg.timeoutSeconds)
                    {
                        op.allowSceneActivation = true; // no dejar la operación colgada
                        yield return Fail($"La carga de '{sceneName}' no avanza desde hace {cfg.timeoutSeconds:0} s.");
                        yield break;
                    }
                    // Carga real → primer tramo de la barra (0–LoadShare)
                    Advance(real * LoadShare, cfg.progressSmoothing);
                    if (Time.unscaledTime >= nextMessage)
                    {
                        message = cfg.RandomMessage(LoadingState.Loading, message);
                        view.SetMessage(message);
                        nextMessage = Time.unscaledTime + cfg.messageInterval;
                    }
                    Tick();
                    yield return null;
                }

                // 2b. Ya cargada pero sin activar: se prolonga a propósito para que se aprecie la pintura (configurable).
                // Es una espera de presentación, no carga: la barra avanza de forma lineal por el resto del recorrido.
                SetState(LoadingState.Activating);
                message = cfg.RandomMessage(LoadingState.Activating, message);
                view.SetMessage(message);
                float wait = Mathf.Max(cfg.postLoadSeconds, cfg.minDisplay - (Time.unscaledTime - started));
                for (float t = 0; t < wait; t += Time.unscaledDeltaTime)
                {
                    Advance(Mathf.Lerp(LoadShare, ActivateShare, t / wait), cfg.progressSmoothing);
                    Tick();
                    yield return null;
                }

                // 3. Activar la escena nueva; hasta que no esté lista, la barra no pasa del 95 %

                op.allowSceneActivation = true;
                while (!op.isDone)
                {
                    Advance(ActivateShare, cfg.progressSmoothing * 2f);
                    Tick();
                    yield return null;
                }
                Time.timeScale = 1f;
                yield return null; // dos fotogramas para que Awake/Start de la escena nueva se asienten
                yield return null;

                // 4. Completar: ahora sí, 100 %
                SetState(LoadingState.Completing);
                message = cfg.RandomMessage(LoadingState.Completing, message);
                view.SetMessage(message);
                for (float t = 0; shown < 0.999f && t < 2f; t += Time.unscaledDeltaTime)
                {
                    Advance(1f, cfg.progressSmoothing);
                    Tick();
                    yield return null;
                }
                shown = 1f; view.SetProgress(1f);
                UIEvents.Play(UISound.LoadingComplete);
                float hold = GameSettings.ReducedMotion ? Mathf.Min(cfg.completionHold, .15f) : cfg.completionHold;
                for (float t = 0; t < hold; t += Time.unscaledDeltaTime) { Tick(); yield return null; }

                // 5. Revelar la escena
                SetState(LoadingState.Revealing);
                yield return FadeView(0f, cfg.exitFade);
                yield return ScreenTransition.Uncover(cfg.uncoverSeconds);
                ok = true;
            }
            finally
            {
                // Pase lo que pase (error, destrucción): nunca dejar la pantalla tapada ni la entrada bloqueada
                if (!ok) Release();
                view.BlocksRaycasts = false;
                loading = false;
                state = LoadingState.Idle;
            }
        }

        /// <summary>Error recuperable: se muestra un mensaje, se registra el motivo y se vuelve a la escena en la que se estaba.</summary>
        IEnumerator Fail(string reason)
        {
            Debug.LogError("SceneLoader: " + reason);
            SetState(LoadingState.Failed);
            view.SetMessage(cfg.RandomMessage(LoadingState.Failed), true);
            for (float t = 0; t < 2.5f; t += Time.unscaledDeltaTime) yield return null;
            Time.timeScale = 1f;
            yield return FadeView(0f, cfg.exitFade);
            yield return ScreenTransition.Uncover(cfg.uncoverSeconds);
        }

        void Release()
        {
            view.Alpha = 0f;
            ScreenTransition.Clear();
            Time.timeScale = 1f;
        }

        LoadingScreenSettings.Variant PickVariant()
        {
            var vs = cfg.variants;
            if (vs == null || vs.Length == 0) return null;
            int v = 0;
            if (vs.Length > 1) do v = Random.Range(0, vs.Length); while (v == lastVariant);
            lastVariant = v;
            return vs[v];
        }

        /// <summary>Sube el progreso visible hacia 'target' (suavizado, sin retroceder, nunca por encima de target).</summary>
        void Advance(float target, float smoothing)
        {
            float k = 1f - Mathf.Exp(-Time.unscaledDeltaTime / Mathf.Max(0.01f, smoothing));
            shown = Mathf.Max(shown, Mathf.Min(target, Mathf.Lerp(shown, target, k)));
            view.SetProgress(shown);
        }

        void Tick() => view.Ambient(GameSettings.ReducedMotion ? 0f : cfg.ambientIntensity);

        IEnumerator FadeView(float target, float seconds)
        {
            if (GameSettings.ReducedMotion) seconds = Mathf.Min(seconds, 0.15f);
            float from = view.Alpha;
            for (float t = 0; t < seconds; t += Time.unscaledDeltaTime)
            {
                view.Alpha = Mathf.Lerp(from, target, cfg.revealCurve.Evaluate(t / seconds));
                Tick();
                yield return null;
            }
            view.Alpha = target;
        }
    }
}
