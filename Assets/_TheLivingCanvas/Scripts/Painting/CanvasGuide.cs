using TheLivingCanvas.Data;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Guía de la plantilla sobre el lienzo: contorno tenue de las zonas y, opcionalmente,
    /// una pista del color sugerido en cada zona. Se compone en la imagen mostrada, no en la pintura.
    /// </summary>
    [RequireComponent(typeof(PaintSurface))]
    public class CanvasGuide : MonoBehaviour
    {
        [SerializeField] Color32 outlineColor = new(70, 45, 30, 90);
        [SerializeField, Range(0f, 1f)] float hintStrength = 0.22f;

        PaintSurface surface;
        PaintTemplate template;
        Color32[] outline;
        Color32[] hints;

        void Awake() => surface = GetComponent<PaintSurface>();

        /// <summary>Cambia la plantilla (null quita la guía).</summary>
        public void SetTemplate(PaintTemplate newTemplate)
        {
            if (newTemplate == template) return;
            template = newTemplate;
            outline = hints = null;
            if (template != null)
                BuildOverlays();
        }

        public void Show(bool showOutline, bool showHints)
        {
            surface.SetGuide(showOutline ? outline : null, showHints ? hints : null);
        }

        void BuildOverlays()
        {
            int w = surface.Width, h = surface.Height;
            int[] zones = template.BuildZoneMap(w, h);
            outline = new Color32[w * h];
            hints = new Color32[w * h];

            var zoneDefs = template.Zones;
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    int i = y * w + x;
                    int zone = zones[i];

                    if (zone >= 0 && zoneDefs[zone].suggestedPigment != null)
                    {
                        Color c = zoneDefs[zone].suggestedPigment.Color;
                        c.a = hintStrength;
                        hints[i] = c;
                    }

                    // Contorno: el píxel toca (8 vecinos) otra zona o el fondo. Da una línea de ~2 px.
                    if (IsBoundary(zones, w, h, x, y, zone))
                        outline[i] = outlineColor;
                }
            }
        }

        static bool IsBoundary(int[] zones, int w, int h, int x, int y, int zone)
        {
            if (zone < 0) return false; // la línea se dibuja solo por dentro de las zonas
            for (int dy = -1; dy <= 1; dy++)
            {
                int ny = y + dy;
                if (ny < 0 || ny >= h) continue;
                for (int dx = -1; dx <= 1; dx++)
                {
                    int nx = x + dx;
                    if (nx < 0 || nx >= w) continue;
                    if (zones[ny * w + nx] != zone) return true;
                }
            }
            return false;
        }
    }
}
