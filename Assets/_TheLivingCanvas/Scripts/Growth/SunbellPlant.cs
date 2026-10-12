using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Sunbell procedural (placeholder), el primer híbrido (girasol + glowbell): un girasol cuyo centro es una esfera
    /// luminosa, con campanillas colgando bajo la flor. Pétalos y campanillas toman el color pintado en "Petals";
    /// al final del crecimiento el centro se enciende con el color de "Glow" y, ya adulta, las campanillas se mecen.
    /// </summary>
    public class SunbellPlant : CropPlant
    {
        static readonly int EmissionColor = Shader.PropertyToID("_EmissionColor");

        [Header("Partes")]
        [SerializeField] Transform growthRoot;
        [SerializeField] Transform[] leafHinges;
        [SerializeField] Transform head;
        [SerializeField] Transform[] petalHinges;
        [SerializeField] Renderer[] petalRenderers;
        [Tooltip("Pivote de cada campanilla, colgando bajo la flor (hijo de GrowthRoot): crece y se mece.")]
        [SerializeField] Transform[] bellPivots;
        [SerializeField] Renderer[] bellRenderers;
        [SerializeField] Renderer[] glowRenderers;
        [SerializeField] Renderer[] stemRenderers;
        [SerializeField] Light glowLight;

        [Header("Zonas de la plantilla")]
        [SerializeField] string petalsZone = "Petals";
        [SerializeField] string glowZone = "Glow";
        [SerializeField] string stemZone = "Stem & leaves";

        [Header("Animación")]
        [SerializeField] float sproutScale = 0.15f;
        [SerializeField] float leafClosedAngle = -80f;
        [SerializeField] float leafOpenAngle = -25f;
        [SerializeField] float petalClosedAngle = 80f;
        [SerializeField] float petalOpenAngle = 5f;
        [Tooltip("Brillo de los pétalos en una Masterpiece.")]
        [SerializeField] float masterpieceGlow = 0.25f;
        [Tooltip("Intensidad de la emisión del centro (Masterpiece brilla más).")]
        [SerializeField] float glowIntensity = 2f;
        [SerializeField] float masterpieceGlowIntensity = 3.5f;
        [SerializeField] float lightIntensity = 1.2f;
        [Tooltip("Vaivén de las campanillas ya crecidas (grados y ciclos por segundo).")]
        [SerializeField] float swayAngle = 6f;
        [SerializeField] float swaySpeed = 0.35f;

        float finalScale = 1f;
        float[] leafYaw;
        Color glowColor = Color.white;
        float maxGlow;
        Material[] glowMaterials;

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
            bool masterpiece = painting.Quality == PaintingQuality.Masterpiece;
            maxGlow = masterpiece ? masterpieceGlowIntensity : glowIntensity;
            glowColor = ZoneColor(painting, glowZone, Color.white);
            var petalColor = ZoneColor(painting, petalsZone, Color.yellow);
            Tint(petalRenderers, petalColor, masterpiece ? masterpieceGlow : 0f);
            Tint(bellRenderers, petalColor);
            Tint(stemRenderers, ZoneColor(painting, stemZone, Color.green));
            Tint(glowRenderers, glowColor);
            glowLight.color = glowColor;

            glowMaterials = new Material[glowRenderers.Length];
            for (int i = 0; i < glowRenderers.Length; i++)
            {
                glowMaterials[i] = glowRenderers[i].material; // instancia propia (creada en Tint)
                glowMaterials[i].EnableKeyword("_EMISSION");
            }
            StartCoroutine(Animate(duration));
        }

        void Update()
        {
            if (!IsGrown) return;
            for (int i = 0; i < bellPivots.Length; i++)
                bellPivots[i].localRotation = Quaternion.Euler(Mathf.Sin((Time.time * swaySpeed + i * 0.3f) * Mathf.PI * 2f) * swayAngle, 0f, 0f);
        }

        protected override void Apply(float t)
        {
            // 0–60 %: crece la planta entera y se despliegan las hojas.
            growthRoot.localScale = Vector3.one * (Mathf.Lerp(sproutScale, 1f, Phase(t, 0f, 0.6f)) * finalScale);
            float leafAngle = Mathf.Lerp(leafClosedAngle, leafOpenAngle, Phase(t, 0.2f, 0.6f));
            for (int i = 0; i < leafHinges.Length; i++)
                leafHinges[i].localRotation = Quaternion.Euler(0f, leafYaw[i], 0f) * Quaternion.Euler(leafAngle, 0f, 0f);

            // 55–100 %: aparece la cabeza y se abren los pétalos. 65–90 %: cuelgan las campanillas.
            head.localScale = Vector3.one * Mathf.Lerp(0.3f, 1f, Phase(t, 0.55f, 0.85f));
            float bloom = Phase(t, 0.65f, 1f);
            foreach (var hinge in petalHinges)
                hinge.localRotation = Quaternion.Euler(Mathf.Lerp(petalClosedAngle, petalOpenAngle, bloom), 0f, 0f);
            float bell = Phase(t, 0.65f, 0.9f);
            foreach (var pivot in bellPivots)
                pivot.localScale = Vector3.one * bell;

            // 85–100 %: se enciende el centro.
            float glow = Phase(t, 0.85f, 1f);
            glowLight.intensity = lightIntensity * glow * finalScale;
            if (glowMaterials == null) return; // aún sin colores (pose inicial del brote)
            foreach (var material in glowMaterials)
                material.SetColor(EmissionColor, glowColor * (maxGlow * glow));
        }
    }
}
