using System;
using UnityEngine;

namespace TheLivingCanvas.Data
{
    public enum ZoneChannel
    {
        Red,
        Green,
        Blue
    }

    /// <summary>Una zona de la plantilla (ej. pétalos) y lo que se espera de ella.</summary>
    [Serializable]
    public class ZoneRequirement
    {
        public string zoneName;
        [Tooltip("Canal de la máscara que marca esta zona.")]
        public ZoneChannel channel;
        [Tooltip("Color sugerido: se usa para la pista de color y para valorar la calidad.")]
        public PigmentDefinition suggestedPigment;
        [Tooltip("Cobertura mínima (0–1) para que la pintura pueda cobrar vida.")]
        [Range(0f, 1f)] public float minCoverage = 0.5f;
        [Tooltip("Peso de la zona en la puntuación final.")]
        public float weight = 1f;
        [Tooltip("Mensaje amable (en inglés) cuando a la zona le falta pintura.")]
        public string missingPaintHint = "This area needs a bit more paint.";
    }

    /// <summary>
    /// Qué debe pintar el jugador y cómo se evalúa: una máscara de zonas (un canal RGB por zona)
    /// del mismo aspecto que el lienzo, más los requisitos de cada zona.
    /// </summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Paint Template", fileName = "Template")]
    public class PaintTemplate : ScriptableObject
    {
        [SerializeField] string displayName;
        [Tooltip("Textura legible (Read/Write), sin compresión ni filtrado.")]
        [SerializeField] Texture2D zoneMask;
        [SerializeField] ZoneRequirement[] zones = Array.Empty<ZoneRequirement>();

        public string DisplayName => displayName;
        public ZoneRequirement[] Zones => zones;

        /// <summary>
        /// Índice de zona por píxel a la resolución pedida: -1 = fuera de toda zona,
        /// 0..n-1 = índice en <see cref="Zones"/>.
        /// </summary>
        public int[] BuildZoneMap(int width, int height)
        {
            var map = new int[width * height];
            var source = zoneMask.GetPixels32();
            int sw = zoneMask.width, sh = zoneMask.height;
            for (int y = 0; y < height; y++)
            {
                int sy = y * sh / height;
                for (int x = 0; x < width; x++)
                {
                    int sx = x * sw / width;
                    map[y * width + x] = ZoneAt(source[sy * sw + sx]);
                }
            }
            return map;
        }

        int ZoneAt(Color32 c)
        {
            for (int z = 0; z < zones.Length; z++)
            {
                byte value = zones[z].channel switch
                {
                    ZoneChannel.Red => c.r,
                    ZoneChannel.Green => c.g,
                    _ => c.b
                };
                if (value > 127) return z;
            }
            return -1;
        }

#if UNITY_EDITOR
        public void EditorSetup(string newDisplayName, Texture2D newZoneMask, ZoneRequirement[] newZones)
        {
            displayName = newDisplayName;
            zoneMask = newZoneMask;
            zones = newZones;
        }
#endif
    }
}
