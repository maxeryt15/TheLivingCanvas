using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Tomatera procedural (placeholder) junto a su tutor: crece, despliega las hojas, cuaja los tomates
    /// y estos maduran de verde al color pintado. Tomates, hojas y tutor toman los colores de cada zona.
    /// </summary>
    public class TomatoPlant : CropPlant
    {
        [Header("Partes")]
        [SerializeField] Transform growthRoot;
        [SerializeField] Transform[] leafHinges;
        [Tooltip("Un pivote por tomate: se escala de 0 a 1 al cuajar.")]
        [SerializeField] Transform[] fruitAnchors;
        [SerializeField] Renderer[] fruitRenderers;
        [SerializeField] Renderer[] leafRenderers;
        [SerializeField] Renderer[] stakeRenderers;

        [Header("Zonas de la plantilla")]
        [SerializeField] string fruitZone = "Tomatoes";
        [SerializeField] string leafZone = "Stem & leaves";
        [SerializeField] string stakeZone = "Stake";

        [Header("Animación")]
        [Tooltip("Tamaño del brote recién plantado (fracción del tamaño adulto).")]
        [SerializeField] float sproutScale = 0.15f;
        [Tooltip("Ángulo de las hojas: plegadas contra el tallo → abiertas.")]
        [SerializeField] float leafClosedAngle = -80f;
        [SerializeField] float leafOpenAngle = -20f;
        [Tooltip("Brillo de los tomates maduros en una Masterpiece.")]
        [SerializeField] float masterpieceGlow = 0.25f;

        float finalScale = 1f;
        float[] leafYaw;
        Color unripeColor = Color.green;
        Color ripeColor = Color.red;
        Material[] fruitMaterials;

        void Awake()
        {
            leafYaw = new float[leafHinges.Length];
            for (int i = 0; i < leafHinges.Length; i++)
                leafYaw[i] = leafHinges[i].localEulerAngles.y;
            Apply(0f); // empieza como brote
        }

        public override void Grow(PaintingResult painting, float duration)
        {
            finalScale = QualityScale(painting.Quality);
            float glow = painting.Quality == PaintingQuality.Masterpiece ? masterpieceGlow : 0f;
            unripeColor = ZoneColor(painting, leafZone, Color.green);
            ripeColor = ZoneColor(painting, fruitZone, Color.red);
            Tint(leafRenderers, unripeColor);
            Tint(stakeRenderers, ZoneColor(painting, stakeZone, new Color(0.55f, 0.33f, 0.13f)));
            Tint(fruitRenderers, ripeColor, glow);

            fruitMaterials = new Material[fruitRenderers.Length];
            for (int i = 0; i < fruitRenderers.Length; i++)
                fruitMaterials[i] = fruitRenderers[i].material; // instancia propia (creada en Tint)
            StartCoroutine(Animate(duration));
        }

        protected override void Apply(float t)
        {
            // 0–60 %: crece la planta y se despliegan las hojas.
            growthRoot.localScale = Vector3.one * (Mathf.Lerp(sproutScale, 1f, Phase(t, 0f, 0.6f)) * finalScale);
            float leafAngle = Mathf.Lerp(leafClosedAngle, leafOpenAngle, Phase(t, 0.15f, 0.6f));
            for (int i = 0; i < leafHinges.Length; i++)
                leafHinges[i].localRotation = Quaternion.Euler(0f, leafYaw[i], 0f) * Quaternion.Euler(leafAngle, 0f, 0f);

            // 50–80 %: cuajan los tomates (verdes). 75–100 %: maduran al color pintado.
            float fruitSize = Phase(t, 0.5f, 0.8f);
            foreach (var anchor in fruitAnchors)
                anchor.localScale = Vector3.one * fruitSize;
            if (fruitMaterials == null) return; // aún sin colores (pose inicial del brote)
            var color = Color.Lerp(unripeColor, ripeColor, Phase(t, 0.75f, 1f));
            foreach (var material in fruitMaterials)
                material.color = color;
        }
    }
}
