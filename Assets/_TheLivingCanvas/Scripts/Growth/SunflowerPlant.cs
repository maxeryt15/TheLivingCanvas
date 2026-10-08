using System.Collections;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Girasol procedural (placeholder): crece de brote a planta completa, despliega las hojas
    /// y abre la flor. Pétalos, centro y tallo toman los colores pintados en cada zona.
    /// </summary>
    public class SunflowerPlant : CropPlant
    {
        [Header("Partes")]
        [SerializeField] Transform growthRoot;
        [SerializeField] Transform[] leafHinges;
        [SerializeField] Transform head;
        [SerializeField] Transform[] petalHinges;
        [SerializeField] Renderer[] petalRenderers;
        [SerializeField] Renderer[] centerRenderers;
        [SerializeField] Renderer[] stemRenderers;

        [Header("Zonas de la plantilla")]
        [SerializeField] string petalsZone = "Petals";
        [SerializeField] string centerZone = "Center";
        [SerializeField] string stemZone = "Stem & leaves";

        [Header("Animación")]
        [Tooltip("Tamaño del brote recién plantado (fracción del tamaño adulto).")]
        [SerializeField] float sproutScale = 0.15f;
        [Tooltip("Ángulo de las hojas: plegadas contra el tallo → abiertas.")]
        [SerializeField] float leafClosedAngle = -80f;
        [SerializeField] float leafOpenAngle = -25f;
        [Tooltip("Ángulo de los pétalos: cerrados hacia delante → abiertos.")]
        [SerializeField] float petalClosedAngle = 80f;
        [SerializeField] float petalOpenAngle = 5f;
        [Tooltip("Brillo de los pétalos en una Masterpiece.")]
        [SerializeField] float masterpieceGlow = 0.25f;

        float finalScale = 1f;
        float[] leafYaw;

        void Awake()
        {
            // Ángulo de cada hoja alrededor del tallo (el pliegue se anima sobre el eje X).
            leafYaw = new float[leafHinges.Length];
            for (int i = 0; i < leafHinges.Length; i++)
                leafYaw[i] = leafHinges[i].localEulerAngles.y;
            Apply(0f); // empieza como brote
        }

        public override void Grow(PaintingResult painting, float duration)
        {
            finalScale = QualityScale(painting.Quality);
            float glow = painting.Quality == PaintingQuality.Masterpiece ? masterpieceGlow : 0f;
            Tint(petalRenderers, ZoneColor(painting, petalsZone, Color.yellow), glow);
            Tint(centerRenderers, ZoneColor(painting, centerZone, new Color(0.45f, 0.3f, 0.15f)));
            Tint(stemRenderers, ZoneColor(painting, stemZone, Color.green));
            StartCoroutine(Animate(duration));
        }

        IEnumerator Animate(float duration)
        {
            for (float time = 0f; time < duration; time += Time.deltaTime)
            {
                Apply(time / duration);
                yield return null;
            }
            Apply(1f);
            IsGrown = true;
        }

        /// <summary>Pose de la planta en el progreso <paramref name="t"/> (0 = brote, 1 = adulta).</summary>
        void Apply(float t)
        {
            // 0–60 %: crece la planta entera y se despliegan las hojas.
            growthRoot.localScale = Vector3.one * (Mathf.Lerp(sproutScale, 1f, Phase(t, 0f, 0.6f)) * finalScale);
            float leafAngle = Mathf.Lerp(leafClosedAngle, leafOpenAngle, Phase(t, 0.2f, 0.6f));
            for (int i = 0; i < leafHinges.Length; i++)
                leafHinges[i].localRotation = Quaternion.Euler(0f, leafYaw[i], 0f) * Quaternion.Euler(leafAngle, 0f, 0f);

            // 55–100 %: aparece la cabeza y se abren los pétalos.
            head.localScale = Vector3.one * Mathf.Lerp(0.3f, 1f, Phase(t, 0.55f, 0.85f));
            float bloom = Phase(t, 0.65f, 1f);
            foreach (var hinge in petalHinges)
                hinge.localRotation = Quaternion.Euler(Mathf.Lerp(petalClosedAngle, petalOpenAngle, bloom), 0f, 0f);
        }
    }
}
