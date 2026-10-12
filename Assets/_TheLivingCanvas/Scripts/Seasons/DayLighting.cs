using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace TheLivingCanvas.Seasons
{
    /// <summary>
    /// Luz según la hora del día: combina el sol de la estación (SeasonVisuals) con una curva de claves horarias y escribe
    /// el sol (que de noche pasa a ser luna), el ambiente, la niebla y el cielo. También da el LampFactor de los faroles.
    /// El cielo usa una instancia del material para no tocar el asset.
    /// </summary>
    public class DayLighting : MonoBehaviour
    {
        [Serializable]
        public struct Key
        {
            [Tooltip("Hora del día; después de medianoche, 24+ (las 2:00 am = 26).")]
            public float hour;
            [Tooltip("Tinte del sol (o de la luna). Se multiplica por el color de la estación según Season Weight.")]
            public Color sunColor;
            [Tooltip("Multiplicador de intensidad: mul × lerp(1, intensidad de la estación, Season Weight).")]
            public float sunIntensityMul;
            [Range(0f, 1f), Tooltip("Cuánto pesa la estación en el sol (1 de día, 0 de noche).")]
            public float seasonWeight;
            [Tooltip("Elevación del sol como fracción de la de mediodía de la estación.")]
            public float elevationMul;
            [Range(0f, 1f), Tooltip("0 = el sol sigue su arco; 1 = la luz está fija en la dirección de la luna.")]
            public float moon;
            public Color ambientSky;
            public Color ambientEquator;
            public Color ambientGround;
            public Color fogColor;
            public float fogDensity;
            [Tooltip("Exposición del cielo procedural.")]
            public float skyExposure;
            public Color skyTint;
            [Tooltip("Tamaño del disco solar; casi 0 apaga el disco.")]
            public float sunSize;
        }

        [SerializeField] SeasonClock clock;
        [SerializeField] SeasonVisuals seasonVisuals;
        [SerializeField] Light sun;
        [Header("Arco del sol")]
        [SerializeField] float sunriseHour = 6f;
        [SerializeField] float sunsetHour = 19.5f;
        [Tooltip("Giro (yaw) de la luz al amanecer y al atardecer: -90 = sol en el este, 90 = en el oeste.")]
        [SerializeField] float sunriseYaw = -75f;
        [SerializeField] float sunsetYaw = 75f;
        [Tooltip("Rotación fija de la luz de noche (la luna, desde arriba).")]
        [SerializeField] Vector3 moonEuler = new Vector3(58f, -30f, 0f);
        [Header("Farolas")]
        [SerializeField] float lampsOnStart = 19f;
        [SerializeField] float lampsOnFull = 20.5f;
        [SerializeField] float lampsOffStart = 6f;
        [SerializeField] float lampsOffEnd = 7f;
        [SerializeField] Key[] keys =
        {
            // 6:00 amanecer: sol bajo al este, crema rosado, ambiente azul grisáceo, algo de bruma.
            new Key { hour = 6f, sunColor = new Color(0.91f, 0.78f, 0.66f), sunIntensityMul = 0.7f, seasonWeight = 1f, elevationMul = 0.2f, moon = 0f,
                      ambientSky = new Color(0.48f, 0.53f, 0.62f), ambientEquator = new Color(0.45f, 0.48f, 0.55f), ambientGround = new Color(0.27f, 0.27f, 0.30f),
                      fogColor = new Color(0.72f, 0.70f, 0.72f), fogDensity = 0.012f,
                      skyExposure = 1f, skyTint = new Color(0.55f, 0.55f, 0.62f), sunSize = 0.04f },
            // 9:00-15:00 día: sol alto, luz neutra, cielo limpio y niebla mínima.
            new Key { hour = 9f, sunColor = Color.white, sunIntensityMul = 1f, seasonWeight = 1f, elevationMul = 1f, moon = 0f,
                      ambientSky = new Color(0.52f, 0.62f, 0.78f), ambientEquator = new Color(0.50f, 0.54f, 0.56f), ambientGround = new Color(0.32f, 0.30f, 0.26f),
                      fogColor = new Color(0.78f, 0.82f, 0.86f), fogDensity = 0.003f,
                      skyExposure = 1.3f, skyTint = new Color(0.5f, 0.5f, 0.5f), sunSize = 0.04f },
            new Key { hour = 15f, sunColor = Color.white, sunIntensityMul = 1f, seasonWeight = 1f, elevationMul = 1f, moon = 0f,
                      ambientSky = new Color(0.52f, 0.62f, 0.78f), ambientEquator = new Color(0.50f, 0.54f, 0.56f), ambientGround = new Color(0.32f, 0.30f, 0.26f),
                      fogColor = new Color(0.78f, 0.82f, 0.86f), fogDensity = 0.003f,
                      skyExposure = 1.3f, skyTint = new Color(0.5f, 0.5f, 0.5f), sunSize = 0.04f },
            // 17:00-18:30 tarde dorada: sol bajo al oeste, amarillo cálido, sombras largas.
            new Key { hour = 17f, sunColor = new Color(0.95f, 0.78f, 0.45f), sunIntensityMul = 0.9f, seasonWeight = 1f, elevationMul = 0.45f, moon = 0f,
                      ambientSky = new Color(0.55f, 0.58f, 0.68f), ambientEquator = new Color(0.55f, 0.50f, 0.44f), ambientGround = new Color(0.34f, 0.29f, 0.22f),
                      fogColor = new Color(0.85f, 0.76f, 0.60f), fogDensity = 0.006f,
                      skyExposure = 1.2f, skyTint = new Color(0.62f, 0.55f, 0.45f), sunSize = 0.05f },
            new Key { hour = 18.5f, sunColor = new Color(0.95f, 0.78f, 0.45f), sunIntensityMul = 0.9f, seasonWeight = 1f, elevationMul = 0.3f, moon = 0f,
                      ambientSky = new Color(0.55f, 0.56f, 0.68f), ambientEquator = new Color(0.55f, 0.48f, 0.42f), ambientGround = new Color(0.33f, 0.27f, 0.21f),
                      fogColor = new Color(0.85f, 0.72f, 0.56f), fogDensity = 0.007f,
                      skyExposure = 1.1f, skyTint = new Color(0.65f, 0.52f, 0.42f), sunSize = 0.05f },
            // 19:30 anochecer: terracota, luz débil, ambiente violeta azulado.
            new Key { hour = 19.5f, sunColor = new Color(0.66f, 0.37f, 0.28f), sunIntensityMul = 0.35f, seasonWeight = 0.8f, elevationMul = 0.1f, moon = 0f,
                      ambientSky = new Color(0.34f, 0.32f, 0.50f), ambientEquator = new Color(0.34f, 0.30f, 0.40f), ambientGround = new Color(0.20f, 0.18f, 0.24f),
                      fogColor = new Color(0.50f, 0.36f, 0.40f), fogDensity = 0.010f,
                      skyExposure = 0.7f, skyTint = new Color(0.55f, 0.38f, 0.38f), sunSize = 0.02f },
            // 21:00-26:30 noche: la luz es la luna (cerúleo tenue, desde arriba); ambiente oscuro pero legible.
            new Key { hour = 21f, sunColor = new Color(0.32f, 0.42f, 0.51f), sunIntensityMul = 0.4f, seasonWeight = 0f, elevationMul = 0.1f, moon = 1f,
                      ambientSky = new Color(0.16f, 0.20f, 0.32f), ambientEquator = new Color(0.14f, 0.17f, 0.27f), ambientGround = new Color(0.09f, 0.10f, 0.15f),
                      fogColor = new Color(0.10f, 0.13f, 0.22f), fogDensity = 0.012f,
                      skyExposure = 0.25f, skyTint = new Color(0.20f, 0.28f, 0.45f), sunSize = 0f },
            new Key { hour = 26.5f, sunColor = new Color(0.32f, 0.42f, 0.51f), sunIntensityMul = 0.4f, seasonWeight = 0f, elevationMul = 0.1f, moon = 1f,
                      ambientSky = new Color(0.16f, 0.20f, 0.32f), ambientEquator = new Color(0.14f, 0.17f, 0.27f), ambientGround = new Color(0.09f, 0.10f, 0.15f),
                      fogColor = new Color(0.10f, 0.13f, 0.22f), fogDensity = 0.012f,
                      skyExposure = 0.25f, skyTint = new Color(0.20f, 0.28f, 0.45f), sunSize = 0f },
        };

        Material sky;
        bool sunDiskOn = true;

        /// <summary>Intensidad de los faroles: 0 de día, sube de las 19:00 a las 20:30 y baja pasado el amanecer.</summary>
        public float LampFactor { get; private set; }

        void Awake()
        {
            // Instancia del cielo: los cambios son de la partida, el asset queda intacto.
            if (RenderSettings.skybox == null) return;
            sky = new Material(RenderSettings.skybox);
            RenderSettings.skybox = sky;
        }

        void OnDestroy()
        {
            if (sky != null) Destroy(sky);
        }

        void Update()
        {
            float hour = HourOfDay();
            Apply(Evaluate(hour), hour);
            LampFactor = Mathf.Max(
                Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(lampsOnStart, lampsOnFull, hour)),
                1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(lampsOffStart, lampsOffEnd, hour)));
        }

        // Los minutos cuentan desde las 6:00.
        float HourOfDay() => 6f + clock.MinutesOfDay / 60f;

        /// <summary>Clave interpolada (con suavizado) para una hora del día.</summary>
        public Key Evaluate(float hour)
        {
            if (hour <= keys[0].hour) return keys[0];
            for (int i = 1; i < keys.Length; i++)
            {
                if (hour > keys[i].hour) continue;
                float k = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(keys[i - 1].hour, keys[i].hour, hour));
                return Lerp(keys[i - 1], keys[i], k);
            }
            return keys[keys.Length - 1];
        }

        static Key Lerp(Key a, Key b, float k) => new Key
        {
            hour = Mathf.Lerp(a.hour, b.hour, k),
            sunColor = Color.Lerp(a.sunColor, b.sunColor, k),
            sunIntensityMul = Mathf.Lerp(a.sunIntensityMul, b.sunIntensityMul, k),
            seasonWeight = Mathf.Lerp(a.seasonWeight, b.seasonWeight, k),
            elevationMul = Mathf.Lerp(a.elevationMul, b.elevationMul, k),
            moon = Mathf.Lerp(a.moon, b.moon, k),
            ambientSky = Color.Lerp(a.ambientSky, b.ambientSky, k),
            ambientEquator = Color.Lerp(a.ambientEquator, b.ambientEquator, k),
            ambientGround = Color.Lerp(a.ambientGround, b.ambientGround, k),
            fogColor = Color.Lerp(a.fogColor, b.fogColor, k),
            fogDensity = Mathf.Lerp(a.fogDensity, b.fogDensity, k),
            skyExposure = Mathf.Lerp(a.skyExposure, b.skyExposure, k),
            skyTint = Color.Lerp(a.skyTint, b.skyTint, k),
            sunSize = Mathf.Lerp(a.sunSize, b.sunSize, k),
        };

        void Apply(Key key, float hour)
        {
            // Sol: color e intensidad son clave × estación; la rotación sigue un arco este → oeste y se funde con la luna.
            sun.color = key.sunColor * Color.Lerp(Color.white, seasonVisuals.SunColor, key.seasonWeight);
            sun.intensity = key.sunIntensityMul * Mathf.Lerp(1f, seasonVisuals.SunIntensity, key.seasonWeight);
            float arc = Mathf.InverseLerp(sunriseHour, sunsetHour, hour);
            var sunRot = Quaternion.Euler(seasonVisuals.SunMiddayElevation * key.elevationMul, Mathf.Lerp(sunriseYaw, sunsetYaw, arc), 0f);
            sun.transform.rotation = Quaternion.Slerp(sunRot, Quaternion.Euler(moonEuler), key.moon);

            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = key.ambientSky;
            RenderSettings.ambientEquatorColor = key.ambientEquator;
            RenderSettings.ambientGroundColor = key.ambientGround;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Exponential;
            RenderSettings.fogColor = key.fogColor;
            RenderSettings.fogDensity = key.fogDensity;

            if (sky == null) return;
            sky.SetFloat("_Exposure", key.skyExposure);
            sky.SetColor("_SkyTint", key.skyTint);
            sky.SetFloat("_SunSize", key.sunSize);
            // El disco se apaga por keyword (cambiar solo la propiedad no basta en runtime).
            bool diskOn = key.sunSize > 0.005f;
            if (diskOn == sunDiskOn) return;
            sunDiskOn = diskOn;
            sky.SetFloat("_SunDisk", diskOn ? 2f : 0f);
            sky.SetKeyword(new LocalKeyword(sky.shader, "_SUNDISK_HIGH_QUALITY"), diskOn);
            sky.SetKeyword(new LocalKeyword(sky.shader, "_SUNDISK_NONE"), !diskOn);
        }
    }
}
