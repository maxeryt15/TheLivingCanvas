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

        /// <summary>Resolución de referencia: el pigmento y el tamaño máximo del pincel se miden respecto a ella.</summary>
        public const int ReferenceWidth = 640;
        public const int ReferenceHeight = 512;
        const int CanvasTolerance = 30 * 30; // distancia RGB² para considerar "tela sin pintar" (como PaintEvaluator)

        // Acuarela: borde más difuso y, al soltar, el color se expande un poco fuera del trazo (a la resolución de referencia).
        const float WashHardness = 0.35f;
        const float BleedPixels = 3f;
        const float BleedStrength = 0.5f; // fracción de la opacidad del trazo que llega al borde del sangrado

        // Remolino: vetas de cerdas que siguen la dirección del trazo. Las vetas solo aclaran (hasta +15 %):
        // oscurecer acercaría el blanco a la tela (236,228,208) y esos píxeles contarían como sin pintar.
        const float StreakAmplitude = 0.15f;
        const float StreakPeriods = 3f;       // vetas a lo ancho del diámetro del pincel
        const float LongStrokeWidths = 0.35f; // un trazo es "largo" si mide al menos esto, en anchos de lienzo

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
        float strokeHardness;
        bool strokeMirror;
        bool strokeBleeds;
        float[] strokeBleed;
        // Remolino: dirección suavizada del trazo (se conserva entre trazos como dirección inicial) y longitud medida en anchos de lienzo.
        bool strokeStreaks;
        Vector2 strokeDirection = Vector2.right;
        float strokeLength;
        float swirlTotalLength, swirlLongLength;
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
        /// <summary>Parte de la longitud pintada con el estilo Remolino que viene de trazos largos (0–1). Deshacer no la descuenta.</summary>
        public float LongStrokeShare => swirlTotalLength > 0f ? swirlLongLength / swirlTotalLength : 0f;
        /// <summary>Longitud total y de trazos largos pintada con Remolino (en anchos de lienzo); se guardan para que <see cref="LongStrokeShare"/> sobreviva.</summary>
        public float SwirlTotalLength => swirlTotalLength;
        public float SwirlLongLength => swirlLongLength;
        public bool CanUndo => history.CanUndo;
        public bool CanRedo => history.CanRedo;

        void Awake()
        {
            meshCollider = GetComponent<MeshCollider>();
            AllocateBuffers();
            GetComponent<MeshRenderer>().material.SetColor("_BaseColor", Color.white);
        }

        /// <summary>
        /// Cambia la resolución (misma superficie física, más o menos píxeles). Solo con la pintura parada:
        /// descarta pintura, guía e historial, que están dimensionados para la resolución anterior.
        /// </summary>
        public void SetResolution(int newWidth, int newHeight)
        {
            if (newWidth == width && newHeight == height) return;
            width = newWidth;
            height = newHeight;
            Destroy(texture);
            AllocateBuffers();
        }

        /// <summary>Crea todo lo que depende del tamaño: píxeles, textura mostrada, historial y búferes de trazo.</summary>
        void AllocateBuffers()
        {
            texture = new Texture2D(width, height, TextureFormat.RGBA32, false)
            {
                name = "PaintTexture",
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear
            };
            pixels = new Color32[width * height];
            // Los demás se crean al usarlos, con el tamaño nuevo.
            display = null;
            strokeBase = null;
            strokeCoverage = null;
            strokeBleed = null;
            strokeBleeds = false;
            guideOutline = guideHints = null;
            history = new PaintHistory(undoSteps);
            FillBase();
            GetComponent<MeshRenderer>().material.SetTexture("_BaseMap", texture);
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
            strokeBleeds = false;
            ResetStrokeLength();
            history.Record(pixels);
            FillBase();
        }

        /// <summary>Lienzo nuevo: en blanco y sin historial (no se puede deshacer).</summary>
        public void ResetToBlank()
        {
            strokeBleeds = false;
            ResetStrokeLength();
            history.Clear();
            FillBase();
        }

        /// <summary>Pone una pintura guardada (del tamaño actual de la superficie): sin historial ni trazo en curso.</summary>
        public void LoadPixels(Color32[] source, float swirlTotal, float swirlLong)
        {
            strokeBleeds = false;
            history.Clear();
            System.Array.Copy(source, pixels, pixels.Length);
            swirlTotalLength = swirlTotal;
            swirlLongLength = swirlLong;
            dirty = true;
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

        public void Undo()
        {
            strokeBleeds = false; // un trazo abandonado no debe sangrar sobre el estado restaurado
            dirty |= history.Undo(pixels);
        }

        public void Redo()
        {
            strokeBleeds = false;
            dirty |= history.Redo(pixels);
        }

        void FillBase()
        {
            for (int i = 0; i < pixels.Length; i++)
                pixels[i] = baseColor;
            dirty = true;
        }

        /// <summary>
        /// Color de la pintura bajo <paramref name="uv"/> (opaco, sin la marca de Fill). Falla sobre tela sin pintar:
        /// no hay nada que copiar.
        /// </summary>
        public bool TrySamplePaint(Vector2 uv, out Color color)
        {
            Vector2 p = UvToPixel(uv);
            Color32 c = pixels[ClampedIndex(p)];
            c.a = 255;
            color = c;
            int dr = c.r - baseColor.r, dg = c.g - baseColor.g, db = c.b - baseColor.b;
            return dr * dr + dg * dg + db * db > CanvasTolerance;
        }

        int ClampedIndex(Vector2 p) =>
            Mathf.Clamp((int)p.y, 0, height - 1) * width + Mathf.Clamp((int)p.x, 0, width - 1);

        /// <summary>
        /// Rellena de golpe la zona de <paramref name="zoneMap"/> que hay bajo <paramref name="uv"/> (un paso de
        /// deshacer). Con <paramref name="mirror"/> rellena también la zona del punto simétrico. Fuera de toda zona
        /// no hace nada; devuelve si rellenó algo.
        /// </summary>
        public bool FillZone(Vector2 uv, int[] zoneMap, Color color, bool mirror = false)
        {
            Vector2 p = UvToPixel(uv);
            int zone = zoneMap[ClampedIndex(p)];
            int mirrorZone = mirror ? zoneMap[ClampedIndex(MirrorPixel(p))] : -1;
            if (zone < 0 && mirrorZone < 0) return false;

            history.Record(pixels);
            Color32 fill = color;
            fill.a = FillAlpha;
            for (int i = 0; i < pixels.Length; i++)
                if (zoneMap[i] >= 0 && (zoneMap[i] == zone || zoneMap[i] == mirrorZone))
                    pixels[i] = fill;
            dirty = true;
            return true;
        }

        /// <param name="opacity">1 = opaco; menos de 1 = veladura que deja ver lo de debajo.</param>
        /// <param name="mirror">Repite cada estampado simétrico respecto al eje vertical central del lienzo.</param>
        /// <param name="bleed">Acuarela: borde difuso y, en <see cref="EndStroke"/>, el color se expande fuera del trazo. Requiere opacidad menor que 1.</param>
        /// <param name="streaks">Remolino: vetas de cerdas a lo largo del trazo; cuenta su longitud para la evaluación.</param>
        public void BeginStroke(Vector2 uv, float radiusPx, Color color, float opacity = 1f, bool mirror = false, bool bleed = false, bool streaks = false)
        {
            history.Record(pixels);
            strokeRadius = radiusPx;
            strokeColor = color;
            strokeMirror = mirror;
            strokeOpacity = Mathf.Clamp01(opacity);
            strokeBleeds = bleed && strokeOpacity < 1f;
            strokeHardness = strokeBleeds ? WashHardness : hardness;
            strokeStreaks = streaks;
            strokeLength = 0f;
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
            if (length >= 1f)
                strokeDirection = Vector2.Lerp(strokeDirection, direction, 0.35f).normalized; // suaviza el temblor del ratón
            if (strokeStreaks) strokeLength += length / width;
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

        /// <summary>
        /// Termina el trazo. En acuarela, los píxeles justo fuera de lo cubierto reciben un poco del color del trazo,
        /// con caída lineal; va dentro del mismo paso de deshacer que el trazo.
        /// </summary>
        public void EndStroke()
        {
            if (strokeStreaks)
            {
                strokeStreaks = false;
                swirlTotalLength += strokeLength;
                if (strokeLength >= LongStrokeWidths) swirlLongLength += strokeLength;
            }
            if (!strokeBleeds) return;
            strokeBleeds = false;

            int reach = Mathf.Max(1, Mathf.RoundToInt(BleedPixels * width / ReferenceWidth));
            if (strokeBleed == null) strokeBleed = new float[pixels.Length];
            else System.Array.Clear(strokeBleed, 0, strokeBleed.Length);

            // Solo los píxeles del borde de lo cubierto reparten sangrado (sus vecinos descubiertos están a 1 px).
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    int i = y * width + x;
                    float edge = strokeCoverage[i];
                    if (edge <= 0f) continue;
                    bool onEdge = (x > 0 && strokeCoverage[i - 1] <= 0f) || (x < width - 1 && strokeCoverage[i + 1] <= 0f)
                        || (y > 0 && strokeCoverage[i - width] <= 0f) || (y < height - 1 && strokeCoverage[i + width] <= 0f);
                    if (!onEdge) continue;

                    float strength = edge * strokeOpacity * BleedStrength;
                    for (int dy = -reach; dy <= reach; dy++)
                    {
                        int py = y + dy;
                        if (py < 0 || py >= height) continue;
                        for (int dx = -reach; dx <= reach; dx++)
                        {
                            int px = x + dx;
                            if (px < 0 || px >= width) continue;
                            float falloff = 1f - Mathf.Sqrt(dx * dx + dy * dy) / (reach + 1f);
                            if (falloff <= 0f) continue;
                            int j = py * width + px;
                            strokeBleed[j] = Mathf.Max(strokeBleed[j], strength * falloff);
                        }
                    }
                }
            }

            for (int i = 0; i < pixels.Length; i++)
            {
                if (strokeBleed[i] <= 0f || strokeCoverage[i] > 0f) continue;
                var bled = Color32.Lerp(pixels[i], strokeColor, strokeBleed[i]);
                bled.a = 255; // pintura a mano: quita la marca de Fill
                pixels[i] = bled;
            }
            dirty = true;
        }

        void ResetStrokeLength()
        {
            strokeStreaks = false;
            swirlTotalLength = swirlLongLength = 0f;
        }

        Vector2 UvToPixel(Vector2 uv) => new(uv.x * width, uv.y * height);

        Vector2 MirrorPixel(Vector2 p) => new(width - p.x, p.y);

        /// <summary>
        /// El reflejo va dentro del mismo trazo: la veladura comparte la cobertura y no se acumula en el eje.
        /// </summary>
        void Stamp(Vector2 center)
        {
            StampDisc(center, strokeDirection);
            if (strokeMirror)
                StampDisc(MirrorPixel(center), new Vector2(-strokeDirection.x, strokeDirection.y));
        }

        static byte Shade(byte channel, float factor) => (byte)Mathf.Clamp(Mathf.RoundToInt(channel * factor), 0, 255);

        void StampDisc(Vector2 center, Vector2 direction)
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

                    float alpha = d <= strokeHardness ? 1f : 1f - (d - strokeHardness) / (1f - strokeHardness);
                    int i = y * width + x;
                    Color32 color = strokeColor;
                    if (strokeStreaks)
                    {
                        // Distancia con signo del píxel a la línea del trazo: las vetas corren a lo largo de la dirección.
                        float across = (dx * -direction.y + dy * direction.x) / r;
                        float shade = 1f + StreakAmplitude * (0.5f + 0.5f * Mathf.Sin(across * Mathf.PI * StreakPeriods));
                        color = new Color32(Shade(strokeColor.r, shade), Shade(strokeColor.g, shade), Shade(strokeColor.b, shade), 255);
                    }
                    if (strokeOpacity < 1f)
                    {
                        float coverage = Mathf.Max(strokeCoverage[i], alpha);
                        strokeCoverage[i] = coverage;
                        var glazed = Color32.Lerp(strokeBase[i], color, coverage * strokeOpacity);
                        glazed.a = 255; // la veladura es trabajo a mano: quita la marca de Fill
                        pixels[i] = glazed;
                    }
                    else
                    {
                        pixels[i] = Color32.Lerp(pixels[i], color, alpha);
                    }
                }
            }
            dirty = true;
        }
    }
}
