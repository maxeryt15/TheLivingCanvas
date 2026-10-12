using System.Collections;
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

        /// <summary>Alcanzó su tamaño final: se puede cosechar.</summary>
        public bool IsGrown { get; protected set; }

        /// <summary>Pose de la planta en el progreso <paramref name="t"/> (0 = brote, 1 = adulta).</summary>
        protected abstract void Apply(float t);

        /// <summary>Recorre la pose de 0 a 1 en <paramref name="duration"/> segundos y queda cosechable.</summary>
        protected IEnumerator Animate(float duration)
        {
            for (float time = 0f; time < duration; time += Time.deltaTime)
            {
                Apply(time / duration);
                yield return null;
            }
            Apply(1f);
            IsGrown = true;
        }

        /// <summary>Unidades cosechadas según la calidad de la pintura.</summary>
        public static int HarvestAmount(PaintingQuality quality) => quality switch
        {
            PaintingQuality.Normal => 1,
            PaintingQuality.Good => 2,
            PaintingQuality.Excellent => 3,
            _ => 4
        };

        /// <summary>Escala final según la calidad de la pintura.</summary>
        protected static float QualityScale(PaintingQuality quality) => quality switch
        {
            PaintingQuality.Normal => 0.85f,
            PaintingQuality.Good => 1f,
            PaintingQuality.Excellent => 1.12f,
            _ => 1.25f
        };

        /// <summary>Color dominante pintado en la zona con ese nombre (o el sugerido si no existe); aclarado si el estilo es pastel.</summary>
        protected static Color ZoneColor(PaintingResult painting, string zoneName, Color fallback)
        {
            Color color = fallback;
            foreach (var zone in painting.Zones)
                if (zone.Requirement.zoneName == zoneName)
                    color = zone.DominantColor;
            return painting.Style != null ? Color.Lerp(color, Color.white, painting.Style.Pastel) : color;
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
