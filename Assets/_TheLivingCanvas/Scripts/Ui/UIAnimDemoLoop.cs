using System.Collections;
using UnityEngine;

namespace TheLivingCanvas.Ui
{
    /// <summary>Solo para la escena de demostración: muestra y oculta el UIAnimator del mismo objeto en bucle.</summary>
    [RequireComponent(typeof(UIAnimator))]
    public class UIAnimDemoLoop : MonoBehaviour
    {
        [SerializeField] float period = 2.6f;
        [SerializeField] float offset;

        IEnumerator Start()
        {
            var a = GetComponent<UIAnimator>();
            yield return new WaitForSecondsRealtime(offset);
            while (true)
            {
                a.Show();
                yield return new WaitForSecondsRealtime(period);
                a.Hide();
                yield return new WaitForSecondsRealtime(period * 0.6f);
            }
        }
    }
}
