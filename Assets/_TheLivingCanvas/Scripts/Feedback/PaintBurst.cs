using UnityEngine;

namespace TheLivingCanvas.Feedback
{
    /// <summary>
    /// Toques de pintura como efecto: pinceladas sueltas (atlas de 4 en el material) que salen al terminar un cuadro,
    /// al madurar una planta y al cosechar. Quien los provoca usa la API estática, que no hace nada si no hay
    /// PaintBurst en la escena; cada efecto es un ParticleSystem que se destruye solo al acabar.
    /// </summary>
    public class PaintBurst : MonoBehaviour
    {
        const int MaxColors = 8; // límite de claves de un Gradient

        [Tooltip("Material de partículas con el atlas 2x2 de pinceladas (alfa mezclado).")]
        [SerializeField] Material dabMaterial;

        static PaintBurst instance;

        void Awake() => instance = this;

        void OnDestroy()
        {
            if (instance == this) instance = null;
        }

        /// <summary>Salpicadura al terminar un cuadro: sale del centro del lienzo hacia <paramref name="outward"/> (el lado del que se pinta).</summary>
        public static void FinishSplash(Vector3 position, Vector3 outward, Color[] colors)
        {
            if (instance == null) return;
            instance.Spawn("FinishSplash", position, outward, colors, 24, ParticleSystemShapeType.Cone, 35f, 0.02f,
                new Vector2(1.5f, 3f), new Vector2(0.8f, 1.3f), new Vector2(0.05f, 0.12f), 0.8f);
        }

        /// <summary>Floritura suave al madurar una planta: pinceladas que suben despacio alrededor de su copa.</summary>
        public static void RipenBloom(Vector3 position, Color[] colors)
        {
            if (instance == null) return;
            instance.Spawn("RipenBloom", position, Vector3.up, colors, 12, ParticleSystemShapeType.Sphere, 0f, 0.15f,
                new Vector2(0.2f, 0.5f), new Vector2(1.2f, 1.8f), new Vector2(0.04f, 0.08f), -0.05f);
        }

        /// <summary>Al cosechar: pinceladas lanzadas hacia el jugador en arco ascendente.</summary>
        public static void HarvestFlurry(Vector3 position, Vector3 towardPlayer, Color[] colors)
        {
            if (instance == null) return;
            instance.Spawn("HarvestFlurry", position, towardPlayer.normalized + Vector3.up * 0.6f, colors, 16, ParticleSystemShapeType.Cone, 25f, 0.02f,
                new Vector2(2f, 3.5f), new Vector2(0.5f, 0.8f), new Vector2(0.04f, 0.09f), 1f);
        }

        /// <summary>Crea y lanza un sistema de una sola ráfaga; cada partícula toma al azar uno de los colores dados.</summary>
        void Spawn(string effectName, Vector3 position, Vector3 direction, Color[] colors, int count,
            ParticleSystemShapeType shape, float angle, float radius,
            Vector2 speed, Vector2 lifetime, Vector2 size, float gravity)
        {
            var effect = new GameObject(effectName);
            effect.transform.SetPositionAndRotation(position, Quaternion.LookRotation(direction));
            var system = effect.AddComponent<ParticleSystem>();
            system.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear); // se configura parado: AddComponent ya lo arranca

            var main = system.main;
            main.duration = 1f;
            main.loop = false;
            main.playOnAwake = false;
            main.stopAction = ParticleSystemStopAction.Destroy;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.gravityModifier = gravity;
            main.startSpeed = new ParticleSystem.MinMaxCurve(speed.x, speed.y);
            main.startLifetime = new ParticleSystem.MinMaxCurve(lifetime.x, lifetime.y);
            main.startSize = new ParticleSystem.MinMaxCurve(size.x, size.y);
            main.startRotation = new ParticleSystem.MinMaxCurve(0f, 2f * Mathf.PI);
            main.startColor = new ParticleSystem.MinMaxGradient(PickGradient(colors)) { mode = ParticleSystemGradientMode.RandomColor };
            main.maxParticles = count;

            var emission = system.emission;
            emission.rateOverTime = 0f;
            emission.SetBursts(new[] { new ParticleSystem.Burst(0f, (short)count) }); // SetBurst(0, ...) no crea la primera

            var shapeModule = system.shape;
            shapeModule.shapeType = shape;
            shapeModule.angle = angle;
            shapeModule.radius = radius;

            // Se desvanecen y encogen un poco hacia el final.
            var fade = new Gradient();
            fade.SetKeys(new[] { new GradientColorKey(Color.white, 0f) },
                new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(1f, 0.5f), new GradientAlphaKey(0f, 1f) });
            var colorOverLifetime = system.colorOverLifetime;
            colorOverLifetime.enabled = true;
            colorOverLifetime.color = new ParticleSystem.MinMaxGradient(fade);
            var sizeOverLifetime = system.sizeOverLifetime;
            sizeOverLifetime.enabled = true;
            sizeOverLifetime.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 1f, 1f, 0.4f));

            // Atlas 2x2: cada partícula elige una de las 4 pinceladas y se queda con ella.
            var sheet = system.textureSheetAnimation;
            sheet.enabled = true;
            sheet.mode = ParticleSystemAnimationMode.Grid;
            sheet.numTilesX = 2;
            sheet.numTilesY = 2;
            sheet.frameOverTime = new ParticleSystem.MinMaxCurve(0f);
            sheet.startFrame = new ParticleSystem.MinMaxCurve(0f, 0.99f);

            effect.GetComponent<ParticleSystemRenderer>().sharedMaterial = dabMaterial;
            system.Play();
        }

        /// <summary>Gradiente "fijo": sus claves son colores sueltos, así que el azar elige uno de ellos y no mezclas.</summary>
        static Gradient PickGradient(Color[] colors)
        {
            if (colors == null || colors.Length == 0) colors = new[] { Color.white };
            int n = Mathf.Min(colors.Length, MaxColors);
            var keys = new GradientColorKey[n];
            for (int i = 0; i < n; i++)
                keys[i] = new GradientColorKey(colors[i], (i + 1f) / n);
            var gradient = new Gradient { mode = GradientMode.Fixed };
            gradient.SetKeys(keys, new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(1f, 1f) });
            return gradient;
        }
    }
}
