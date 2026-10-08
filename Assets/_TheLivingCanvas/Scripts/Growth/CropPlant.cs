using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Planta 3D que crece de una parcela. Cada partida se tiñe con el color dominante
    /// que el jugador pintó en la zona correspondiente de la plantilla.
    /// </summary>
    public abstract class CropPlant : MonoBehaviour
    {
        static readonly int EmissionColor = Shader.PropertyToID("_EmissionColor");

        /// <summary>Empieza a crecer: <paramref name="duration"/> segundos hasta el tamaño final.</summary>
        public abstract void Grow(PaintingResult painting, float duration);

        /// <summary>Escala final según la calidad de la pintura.</summary>
        protected static float QualityScale(PaintingQuality quality) => quality switch
        {
            PaintingQuality.Normal => 0.85f,
            PaintingQuality.Good => 1f,
            PaintingQuality.Excellent => 1.12f,
            _ => 1.25f
        };

        /// <summary>Color dominante pintado en la zona con ese nombre (o el sugerido si no existe).</summary>
        protected static Color ZoneColor(PaintingResult painting, string zoneName, Color fallback)
        {
            foreach (var zone in painting.Zones)
                if (zone.Requirement.zoneName == zoneName)
                    return zone.DominantColor;
            return fallback;
        }

        protected static void Tint(Renderer[] renderers, Color color, float glow = 0f)
        {
            foreach (var r in renderers)
            {
                var material = r.material; // instancia propia por planta
                material.color = color;
                if (glow <= 0f) continue;
                material.EnableKeyword("_EMISSION");
                material.SetColor(EmissionColor, color * glow);
            }
        }

        /// <summary>0→1 suave entre <paramref name="from"/> y <paramref name="to"/>.</summary>
        protected static float Phase(float t, float from, float to) => Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(from, to, t));
    }
}
