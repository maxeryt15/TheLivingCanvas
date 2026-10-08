using UnityEngine;

namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Objeto de prueba (Fase 1C): enciende y apaga una luz. Se quitará cuando haya interactuables reales.
    /// </summary>
    public class TestLamp : MonoBehaviour, IInteractable
    {
        [SerializeField] Light lampLight;
        [SerializeField] Renderer bulb;
        [SerializeField] Color onColor = new(1f, 0.85f, 0.55f);
        [SerializeField] Color offColor = new(0.35f, 0.33f, 0.3f);
        [SerializeField] bool isOn;

        public string Prompt => isOn ? "Turn off lamp" : "Turn on lamp";
        public bool CanInteract => true;

        void Start() => Apply();

        public void Interact(PlayerInteractor interactor)
        {
            isOn = !isOn;
            Apply();
        }

        void Apply()
        {
            lampLight.enabled = isOn;
            bulb.material.color = isOn ? onColor : offColor;
        }
    }
}
