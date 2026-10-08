using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Superficie pintable de un lienzo: textura en CPU (Color32[]) mostrada en el material del Quad.
    /// Los trazos estampan el pincel a intervalos regulares para que no queden huecos.
    /// </summary>
    [RequireComponent(typeof(MeshCollider), typeof(MeshRenderer))]
    public class PaintSurface : MonoBehaviour
    {
        [Tooltip("Resolución de la pintura. Mantener la proporción del lienzo (1 × 0.8 m → 5:4).")]
        [SerializeField] int width = 640;
        [SerializeField] int height = 512;
        [Tooltip("Color de la tela sin pintar (también es lo que pinta el borrador).")]
        [SerializeField] Color32 baseColor = new(236, 228, 208, 255);
        [Tooltip("Separación entre estampados, como fracción del radio.")]
        [SerializeField, Range(0.05f, 1f)] float spacing = 0.25f;
        [Tooltip("Parte del radio que se pinta a opacidad completa; el resto se difumina.")]
        [SerializeField, Range(0f, 1f)] float hardness = 0.7f;
        [Tooltip("Pasos de deshacer (cada uno ocupa ancho × alto × 4 bytes).")]
        [SerializeField] int undoSteps = 20;

        MeshCollider meshCollider;
        PaintHistory history;
        Texture2D texture;
        Color32[] pixels;
        bool dirty;

        // Estado del trazo en curso.
        Vector2 lastPixel;
        float distanceSinceStamp;
        float strokeRadius;
        Color32 strokeColor;

        /// <summary>Tamaño en metros de un píxel de la pintura (para dibujar el cursor a escala).</summary>
        public float PixelWorldSize => transform.lossyScale.x / width;

        public Color BaseColor => baseColor;
        public int Width => width;
        public int Height => height;
        /// <summary>Aumenta con cada cambio de la pintura (para recalcular análisis solo cuando hace falta).</summary>
        public int Revision { get; private set; }
        /// <summary>Píxeles actuales, solo lectura por convención (análisis de cobertura).</summary>
        internal Color32[] Pixels => pixels;
        public bool CanUndo => history.CanUndo;
        public bool CanRedo => history.CanRedo;

        void Awake()
        {
            meshCollider = GetComponent<MeshCollider>();
            texture = new Texture2D(width, height, TextureFormat.RGBA32, false)
            {
                name = "PaintTexture",
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear
            };
            pixels = new Color32[width * height];
            history = new PaintHistory(undoSteps);
            FillBase();

            var material = GetComponent<MeshRenderer>().material;
            material.SetTexture("_BaseMap", texture);
            material.SetColor("_BaseColor", Color.white);
        }

        void OnDestroy() => Destroy(texture);

        void LateUpdate()
        {
            if (!dirty) return;
            texture.SetPixels32(pixels);
            texture.Apply(false);
            dirty = false;
            Revision++;
        }

        /// <summary>Raycast solo contra este lienzo. Devuelve la UV (0–1) del punto tocado.</summary>
        public bool Raycast(Ray ray, out Vector2 uv, out RaycastHit hit, float maxDistance = 10f)
        {
            bool didHit = meshCollider.Raycast(ray, out hit, maxDistance);
            uv = didHit ? hit.textureCoord : default;
            return didHit;
        }

        /// <summary>Deja el lienzo en blanco (se puede deshacer).</summary>
        public void Clear()
        {
            history.Record(pixels);
            FillBase();
        }

        public void Undo() => dirty |= history.Undo(pixels);

        public void Redo() => dirty |= history.Redo(pixels);

        void FillBase()
        {
            for (int i = 0; i < pixels.Length; i++)
                pixels[i] = baseColor;
            dirty = true;
        }

        public void BeginStroke(Vector2 uv, float radiusPx, Color color)
        {
            history.Record(pixels);
            strokeRadius = radiusPx;
            strokeColor = color;
            lastPixel = UvToPixel(uv);
            distanceSinceStamp = 0f;
            Stamp(lastPixel);
        }

        public void ContinueStroke(Vector2 uv)
        {
            Vector2 target = UvToPixel(uv);
            Vector2 delta = target - lastPixel;
            float length = delta.magnitude;
            if (length < 0.001f) return;

            Vector2 direction = delta / length;
            float step = Mathf.Max(1f, strokeRadius * spacing);
            float travelled = step - distanceSinceStamp;
            while (travelled <= length)
            {
                Stamp(lastPixel + direction * travelled);
                travelled += step;
            }
            distanceSinceStamp = length - (travelled - step);
            lastPixel = target;
        }

        Vector2 UvToPixel(Vector2 uv) => new(uv.x * width, uv.y * height);

        void Stamp(Vector2 center)
        {
            float r = strokeRadius;
            int xMin = Mathf.Max(0, Mathf.FloorToInt(center.x - r));
            int xMax = Mathf.Min(width - 1, Mathf.CeilToInt(center.x + r));
            int yMin = Mathf.Max(0, Mathf.FloorToInt(center.y - r));
            int yMax = Mathf.Min(height - 1, Mathf.CeilToInt(center.y + r));

            for (int y = yMin; y <= yMax; y++)
            {
                for (int x = xMin; x <= xMax; x++)
                {
                    float dx = x + 0.5f - center.x;
                    float dy = y + 0.5f - center.y;
                    float d = Mathf.Sqrt(dx * dx + dy * dy) / r;
                    if (d > 1f) continue;

                    float alpha = d <= hardness ? 1f : 1f - (d - hardness) / (1f - hardness);
                    int i = y * width + x;
                    pixels[i] = Color32.Lerp(pixels[i], strokeColor, alpha);
                }
            }
            dirty = true;
        }
    }
}
