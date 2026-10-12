using System;
using System.Collections.Generic;
using UnityEngine;

namespace TheLivingCanvas.Seasons
{
    /// <summary>
    /// Cambia el paisaje con la estación: tono del follaje y del suelo, y el sol de la estación (color, intensidad y
    /// elevación a mediodía, ya mezclados en las transiciones), que luego combina DayLighting con la hora. Cada material se acerca al color de la estación según su mezcla (0 = su color original), por
    /// MaterialPropertyBlock en _BaseColor; nunca se tocan los .mat.
    /// </summary>
    public class SeasonVisuals : MonoBehaviour
    {
        [Serializable]
        public struct Look
        {
            public Color sunColor;
            public float sunIntensity;
            [Range(5f, 80f)] public float sunMiddayElevation;
            public Color foliageColor;
            [Range(0f, 1f)] public float foliageBlend;
            public Color groundColor;
            [Range(0f, 1f)] public float groundBlend;
        }

        [SerializeField] SeasonClock clock;
        [SerializeField] Material[] foliageMaterials;
        [SerializeField] Material[] groundMaterials;
        [SerializeField] float transitionSeconds = 4f;
        // Orden del enum Season: Spring, Summer, Autumn, Winter.
        [SerializeField] Look[] looks =
        {
            new Look { sunColor = new Color(1f, 0.92f, 0.80f), sunIntensity = 1.5f, sunMiddayElevation = 45f,
                       foliageColor = Color.white, foliageBlend = 0f, groundColor = Color.white, groundBlend = 0f },
            new Look { sunColor = new Color(1f, 0.88f, 0.72f), sunIntensity = 1.7f, sunMiddayElevation = 58f,
                       foliageColor = new Color(0.30f, 0.45f, 0.15f), foliageBlend = 0.3f, groundColor = new Color(0.55f, 0.58f, 0.30f), groundBlend = 0.3f },
            new Look { sunColor = new Color(1f, 0.76f, 0.52f), sunIntensity = 1.4f, sunMiddayElevation = 30f,
                       foliageColor = new Color(0.58f, 0.33f, 0.12f), foliageBlend = 0.75f, groundColor = new Color(0.56f, 0.48f, 0.28f), groundBlend = 0.5f },
            new Look { sunColor = new Color(0.82f, 0.88f, 1f), sunIntensity = 1.15f, sunMiddayElevation = 22f,
                       foliageColor = new Color(0.30f, 0.38f, 0.36f), foliageBlend = 0.7f, groundColor = new Color(0.80f, 0.83f, 0.82f), groundBlend = 0.7f },
        };

        struct Target
        {
            public Renderer renderer;
            public int index;
            public Color original;
            public bool foliage;
        }

        readonly List<Target> targets = new List<Target>();
        MaterialPropertyBlock block;
        Look from, to;
        float t = 1f;

        /// <summary>Color del sol de la estación actual (mezclado durante la transición).</summary>
        public Color SunColor => Current().sunColor;
        /// <summary>Intensidad del sol de la estación actual.</summary>
        public float SunIntensity => Current().sunIntensity;
        /// <summary>Elevación del sol a mediodía, en grados.</summary>
        public float SunMiddayElevation => Current().sunMiddayElevation;

        void Start()
        {
            block = new MaterialPropertyBlock();
            Collect(foliageMaterials, true);
            Collect(groundMaterials, false);
            to = looks[(int)clock.Current];
            t = 1f; // una carga de partida pudo disparar SeasonChanged antes: se queda en la estación actual, sin transición
            Apply(to);
        }

        void OnEnable() => clock.SeasonChanged += OnSeasonChanged;

        void OnDisable() => clock.SeasonChanged -= OnSeasonChanged;

        // Guarda el color original de cada (renderer, slot) cuyo sharedMaterial esté en la lista.
        void Collect(Material[] materials, bool foliage)
        {
            foreach (var r in FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                var shared = r.sharedMaterials;
                for (int i = 0; i < shared.Length; i++)
                    if (shared[i] != null && Array.IndexOf(materials, shared[i]) >= 0)
                        targets.Add(new Target { renderer = r, index = i, original = shared[i].GetColor("_BaseColor"), foliage = foliage });
            }
        }

        void OnSeasonChanged(Season season)
        {
            from = Current();
            to = looks[(int)season];
            t = 0f;
        }

        void Update()
        {
            if (t >= 1f) return;
            t = Mathf.Min(1f, t + Time.deltaTime / transitionSeconds);
            Apply(Current());
        }

        Look Current() => t >= 1f ? to : Lerp(from, to, t);

        static Look Lerp(Look a, Look b, float k) => new Look
        {
            sunColor = Color.Lerp(a.sunColor, b.sunColor, k),
            sunIntensity = Mathf.Lerp(a.sunIntensity, b.sunIntensity, k),
            sunMiddayElevation = Mathf.Lerp(a.sunMiddayElevation, b.sunMiddayElevation, k),
            foliageColor = Color.Lerp(a.foliageColor, b.foliageColor, k),
            foliageBlend = Mathf.Lerp(a.foliageBlend, b.foliageBlend, k),
            groundColor = Color.Lerp(a.groundColor, b.groundColor, k),
            groundBlend = Mathf.Lerp(a.groundBlend, b.groundBlend, k),
        };

        void Apply(Look look)
        {
            foreach (var target in targets)
            {
                if (target.renderer == null) continue;
                var color = target.foliage
                    ? Color.Lerp(target.original, look.foliageColor, look.foliageBlend)
                    : Color.Lerp(target.original, look.groundColor, look.groundBlend);
                block.Clear();
                block.SetColor("_BaseColor", color);
                target.renderer.SetPropertyBlock(block, target.index);
            }
        }
    }
}
