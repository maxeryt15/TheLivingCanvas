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
        /// <summary>
        /// Alfa con que el pincel Fill marca sus píxeles (el resto de la pintura usa 255). Va dentro del propio
        /// píxel, así deshacer/rehacer lo conserva; pintar encima a mano lo devuelve a 255. El lienzo es opaco.
        /// </summary>
        public const byte FillAlpha = 254;

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

        // Guía opcional (contorno y pistas de color): solo afecta a la imagen mostrada.
        Color32[] guideOutline;
        Color32[] guideHints;
        Color32[] display;
        Texture2D texture;
        Color32[] pixels;
        bool dirty;

        // Estado del trazo en curso.
        Vector2 lastPixel;
        float distanceSinceStamp;
        float strokeRadius;
        Color32 strokeColor;
        // Veladura (opacidad < 1): se mezcla con la pintura de antes del trazo y cada píxel guarda la cobertura
        // máxima del trazo, así los estampados que se solapan dentro de un mismo trazo no se acumulan.
        float strokeOpacity = 1f;
        Color32[] strokeBase;
        float[] strokeCoverage;

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
            texture.SetPixels32(guideOutline == null && guideHints == null ? pixels : ComposeDisplay());
            texture.Apply(false);
            dirty = false;
            Revision++;
        }

        /// <summary>
        /// Capas de guía por píxel (alfa = intensidad). Las pistas de color solo se ven sobre tela sin pintar;
        /// el contorno se ve siempre, tenue. null quita la capa.
        /// </summary>
        public void SetGuide(Color32[] outline, Color32[] hints)
        {
            guideOutline = outline;
            guideHints = hints;
            dirty = true;
        }

        Color32[] ComposeDisplay()
        {
            display ??= new Color32[pixels.Length];
            for (int i = 0; i < pixels.Length; i++)
            {
                Color32 c = pixels[i];
                if (guideHints != null && guideHints[i].a > 0 && IsBase(c))
                    c = Color32.Lerp(c, guideHints[i], guideHints[i].a / 255f);
                if (guideOutline != null && guideOutline[i].a > 0)
                    c = Color32.Lerp(c, guideOutline[i], guideOutline[i].a / 255f);
                c.a = 255;
                display[i] = c;
            }
            return display;
        }

        bool IsBase(Color32 c) => c.r == baseColor.r && c.g == baseColor.g && c.b == baseColor.b;

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

        /// <summary>Lienzo nuevo: en blanco y sin historial (no se puede deshacer).</summary>
        public void ResetToBlank()
        {
            history.Clear();
            FillBase();
        }

        /// <summary>Copia de la pintura actual (sin la guía) como textura independiente.</summary>
        public Texture2D CreateSnapshot()
        {
            var snapshot = new Texture2D(width, height, TextureFormat.RGBA32, false)
            {
                name = "PaintingSnapshot",
                wrapMode = TextureWrapMode.Clamp
            };
            snapshot.SetPixels32(pixels);
            snapshot.Apply(false);
            return snapshot;
        }

        public void Undo() => dirty |= history.Undo(pixels);

        public void Redo() => dirty |= history.Redo(pixels);

        void FillBase()
        {
            for (int i = 0; i < pixels.Length; i++)
                pixels[i] = baseColor;
            dirty = true;
        }

        /// <summary>
        /// Rellena de golpe la zona de <paramref name="zoneMap"/> que hay bajo <paramref name="uv"/> (un paso de
        /// deshacer). Fuera de toda zona no hace nada; devuelve si rellenó algo.
        /// </summary>
        public bool FillZone(Vector2 uv, int[] zoneMap, Color color)
        {
            Vector2 p = UvToPixel(uv);
            int x = Mathf.Clamp((int)p.x, 0, width - 1), y = Mathf.Clamp((int)p.y, 0, height - 1);
            int zone = zoneMap[y * width + x];
            if (zone < 0) return false;

            history.Record(pixels);
            Color32 fill = color;
            fill.a = FillAlpha;
            for (int i = 0; i < pixels.Length; i++)
                if (zoneMap[i] == zone)
                    pixels[i] = fill;
            dirty = true;
            return true;
        }

        /// <param name="opacity">1 = opaco; menos de 1 = veladura que deja ver lo de debajo.</param>
        public void BeginStroke(Vector2 uv, float radiusPx, Color color, float opacity = 1f)
        {
            history.Record(pixels);
            strokeRadius = radiusPx;
            strokeColor = color;
            strokeOpacity = Mathf.Clamp01(opacity);
            if (strokeOpacity < 1f)
            {
                strokeBase ??= new Color32[pixels.Length];
                strokeCoverage ??= new float[pixels.Length];
                System.Array.Copy(pixels, strokeBase, pixels.Length);
                System.Array.Clear(strokeCoverage, 0, strokeCoverage.Length);
            }
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
                    if (strokeOpacity < 1f)
                    {
                        float coverage = Mathf.Max(strokeCoverage[i], alpha);
                        strokeCoverage[i] = coverage;
                        var glazed = Color32.Lerp(strokeBase[i], strokeColor, coverage * strokeOpacity);
                        glazed.a = 255; // la veladura es trabajo a mano: quita la marca de Fill
                        pixels[i] = glazed;
                    }
                    else
                    {
                        pixels[i] = Color32.Lerp(pixels[i], strokeColor, alpha);
                    }
                }
            }
            dirty = true;
        }
    }
}
