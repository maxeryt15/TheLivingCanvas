using UnityEngine;
using UnityEngine.EventSystems;

namespace TheLivingCanvas.Ui
{
    /// <summary>Anuncia a UIEvents el sonido de un botón: Hover al pasar el ratón, Select al enfocarlo con teclado/mando y Confirm al pulsarlo.</summary>
    public class UIButtonSound : MonoBehaviour, IPointerEnterHandler, ISelectHandler, IPointerClickHandler, ISubmitHandler
    {
        public void OnPointerEnter(PointerEventData e) => UIEvents.Play(UISound.Hover);
        public void OnSelect(BaseEventData e) { if (!(e is PointerEventData)) UIEvents.Play(UISound.Select); }
        public void OnPointerClick(PointerEventData e) => UIEvents.Play(UISound.Confirm);
        public void OnSubmit(BaseEventData e) => UIEvents.Play(UISound.Confirm);
    }
}
