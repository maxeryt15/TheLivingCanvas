using UnityEngine;
using UnityEngine.Rendering;

namespace TheLivingCanvas.Art
{
    /// <summary>
    /// Controla la Descoloración de una zona: fija el global de shader <c>_TLC_Descolor</c> (lo leen los materiales
    /// TLC/Painterly) y el peso de un Volume de atmósfera (saturación, balance cálido/frío, contraste).
    /// 0 = color normal, 1 = Descoloración completa. En el editor, mueve <see cref="amount"/> para ajustarlo en vivo.
    /// Limitación: el global afecta a TODOS los materiales Painterly a la vez; para zonas distintas habrá que
    /// pasar a un valor por zona (MaterialPropertyBlock o volumen local). Se hará cuando el prototipo se apruebe.
    /// </summary>
    [ExecuteAlways]
    public class PainterlyDescolor : MonoBehaviour
    {
        static readonly int DescolorId = Shader.PropertyToID("_TLC_Descolor");

        [Range(0f, 1f)] public float amount;
        [Tooltip("Segundos que tarda la transición al usar SetTarget.")]
        public float transitionSeconds = 2.5f;
        [Tooltip("Volume global cuyo peso sigue a 'amount' (perfil con los ajustes de atmósfera de la Descoloración).")]
        public Volume atmosphere;

        float _target = -1f;

        public float Amount => amount;

        public void SetTarget(float value)
        {
            _target = Mathf.Clamp01(value);
            if (!Application.isPlaying || transitionSeconds <= 0f)
            {
                amount = _target;
                _target = -1f;
            }
        }

        public void Toggle()
        {
            var goal = _target >= 0f ? _target : amount;
            SetTarget(goal > 0.5f ? 0f : 1f);
        }

        void Update()
        {
            if (Application.isPlaying && _target >= 0f)
            {
                amount = Mathf.MoveTowards(amount, _target, Time.deltaTime / transitionSeconds);
                if (Mathf.Approximately(amount, _target)) _target = -1f;
            }
            Apply();
        }

        void OnValidate() => Apply();

        void OnDisable() => Shader.SetGlobalFloat(DescolorId, 0f);

        void Apply()
        {
            Shader.SetGlobalFloat(DescolorId, amount);
            if (atmosphere != null) atmosphere.weight = Mathf.SmoothStep(0f, 1f, amount);
        }
    }
}
