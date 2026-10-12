using UnityEngine;

namespace TheLivingCanvas.Seasons
{
    /// <summary>
    /// Farol o lámpara que se enciende al anochecer: intensidad = lerp(día, noche, DayLighting.LampFactor) y, si hay,
    /// el color de su bombilla por MaterialPropertyBlock. La luz es opcional (hay farolas solo con bombilla) y se
    /// desactiva mientras está apagada para no gastar luces en tiempo real.
    /// </summary>
    public class NightLamp : MonoBehaviour
    {
        [SerializeField] DayLighting dayLighting;
        [SerializeField] Light lampLight;
        [SerializeField] float dayIntensity;
        [SerializeField] float nightIntensity = 2f;
        [SerializeField] Renderer bulb;
        [SerializeField] Color bulbDayColor = new Color(0.45f, 0.40f, 0.30f);
        [SerializeField, ColorUsage(false, true)] Color bulbNightColor = new Color(2.4f, 1.7f, 0.9f);

        MaterialPropertyBlock block;
        float lastFactor = -1f;

        void Update()
        {
            float factor = dayLighting.LampFactor;
            if (Mathf.Approximately(factor, lastFactor)) return;
            lastFactor = factor;
            if (lampLight != null)
            {
                lampLight.intensity = Mathf.Lerp(dayIntensity, nightIntensity, factor);
                lampLight.enabled = lampLight.intensity > 0.01f;
            }
            if (bulb == null) return;
            block ??= new MaterialPropertyBlock();
            block.SetColor("_BaseColor", Color.Lerp(bulbDayColor, bulbNightColor, factor));
            bulb.SetPropertyBlock(block);
        }
    }
}
