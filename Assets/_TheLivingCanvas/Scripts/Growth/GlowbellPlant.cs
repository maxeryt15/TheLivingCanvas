using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Glowbell procedural (placeholder), el primer cultivo fantástico: un tallo con ramas arqueadas de las
    /// que cuelgan campanillas con una esfera luminosa debajo. Al final del crecimiento se encienden las luces
    /// (del color pintado en la zona "Glow") y, ya adulta, las campanillas se mecen.
    /// </summary>
    public class GlowbellPlant : CropPlant
    {
        static readonly int EmissionColor = Shader.PropertyToID("_EmissionColor");

        [Header("Partes")]
        [SerializeField] Transform growthRoot;
        [SerializeField] Transform[] leafHinges;
        [Tooltip("Una por rama: se escala de 0 a 1 al brotar.")]
        [SerializeField] Transform[] branchPivots;
        [Tooltip("Pivote de cada campanilla, colgando en la punta de su rama (hijo de GrowthRoot, no de la rama): crece y se mece.")]
        [SerializeField] Transform[] bellPivots;
        [SerializeField] Renderer[] bellRenderers;
        [SerializeField] Renderer[] glowRenderers;
        [SerializeField] Renderer[] stemRenderers;
        [SerializeField] Light glowLight;

        [Header("Zonas de la plantilla")]
        [SerializeField] string bellZone = "Bells";
        [SerializeField] string glowZone = "Glow";
        [SerializeField] string stemZone = "Stem & leaves";

        [Header("Animación")]
        [SerializeField] float sproutScale = 0.15f;
        [SerializeField] float leafClosedAngle = -80f;
        [SerializeField] float leafOpenAngle = -25f;
        [Tooltip("Intensidad de la emisión de las esferas (Masterpiece brilla más).")]
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
            maxGlow = painting.Quality == PaintingQuality.Masterpiece ? masterpieceGlowIntensity : glowIntensity;
            glowColor = ZoneColor(painting, glowZone, Color.white);
            Tint(bellRenderers, ZoneColor(painting, bellZone, new Color(0.17f, 0.27f, 0.62f)));
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
            // 0–60 %: crece la planta y se despliegan las hojas.
            growthRoot.localScale = Vector3.one * (Mathf.Lerp(sproutScale, 1f, Phase(t, 0f, 0.6f)) * finalScale);
            float leafAngle = Mathf.Lerp(leafClosedAngle, leafOpenAngle, Phase(t, 0.15f, 0.55f));
            for (int i = 0; i < leafHinges.Length; i++)
                leafHinges[i].localRotation = Quaternion.Euler(0f, leafYaw[i], 0f) * Quaternion.Euler(leafAngle, 0f, 0f);

            // 30–70 %: brotan las ramas. 65–90 %: cuelgan las campanillas (con la rama ya casi entera).
            float branch = Phase(t, 0.3f, 0.7f);
            foreach (var pivot in branchPivots)
                pivot.localScale = Vector3.one * branch;
            float bell = Phase(t, 0.65f, 0.9f);
            foreach (var pivot in bellPivots)
                pivot.localScale = Vector3.one * bell;

            // 85–100 %: se encienden.
            float glow = Phase(t, 0.85f, 1f);
            glowLight.intensity = lightIntensity * glow * finalScale;
            if (glowMaterials == null) return; // aún sin colores (pose inicial del brote)
            foreach (var material in glowMaterials)
                material.SetColor(EmissionColor, glowColor * (maxGlow * glow));
        }
    }
}
