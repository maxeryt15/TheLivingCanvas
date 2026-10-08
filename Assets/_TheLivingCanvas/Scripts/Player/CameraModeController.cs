using Unity.Cinemachine;
using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Player
{
    public enum CameraMode
    {
        ThirdPerson,
        FirstPerson,
        /// <summary>Primera persona fija en un punto (ej. frente al lienzo al pintar).</summary>
        FixedView
    }

    /// <summary>
    /// Cámara contextual: tercera persona por defecto y primera persona para acciones
    /// puntuales (pintar, inspeccionar pinturas). Cambia la prioridad entre CinemachineCameras
    /// y deja quieto al jugador mientras no está en tercera persona.
    /// </summary>
    public class CameraModeController : MonoBehaviour
    {
        const int ActivePriority = 10;
        const int InactivePriority = 0;

        [SerializeField] CinemachineCamera thirdPersonCamera;
        [SerializeField] CinemachineCamera firstPersonCamera;
        [Tooltip("Cámara sin movimiento propio; se coloca en el punto de vista pedido.")]
        [SerializeField] CinemachineCamera fixedViewCamera;
        [SerializeField] PlayerMovement playerMovement;
        [Tooltip("Se oculta en primera persona para que el cuerpo no tape la vista.")]
        [SerializeField] GameObject playerVisuals;
        [Tooltip("Temporal (Fase 1B): alterna la vista para probar. Lo reemplazarán las interacciones.")]
        [SerializeField] InputActionReference debugToggleAction;

        CinemachineInputAxisController thirdPersonInput;
        CinemachineInputAxisController firstPersonInput;
        CinemachinePanTilt firstPersonPanTilt;
        CameraMode modeBeforeFixedView;
        bool lookInputEnabled = true;

        public CameraMode Mode { get; private set; }

        /// <summary>Permite apagar el mirar con ratón/stick (ej. con el inventario abierto para usar el cursor).</summary>
        public void SetLookInputEnabled(bool enabled)
        {
            lookInputEnabled = enabled;
            ApplyLookInput();
        }

        void ApplyLookInput()
        {
            // Solo la cámara activa lee el ratón/stick.
            thirdPersonInput.enabled = Mode == CameraMode.ThirdPerson && lookInputEnabled;
            firstPersonInput.enabled = Mode == CameraMode.FirstPerson && lookInputEnabled;
        }

        void Awake()
        {
            thirdPersonInput = thirdPersonCamera.GetComponent<CinemachineInputAxisController>();
            firstPersonInput = firstPersonCamera.GetComponent<CinemachineInputAxisController>();
            firstPersonPanTilt = firstPersonCamera.GetComponent<CinemachinePanTilt>();
        }

        void OnEnable()
        {
            if (debugToggleAction == null) return;
            debugToggleAction.action.Enable();
            debugToggleAction.action.performed += OnDebugToggle;
        }

        void OnDisable()
        {
            if (debugToggleAction == null) return;
            debugToggleAction.action.performed -= OnDebugToggle;
        }

        void Start() => SetMode(CameraMode.ThirdPerson);

        void OnDebugToggle(InputAction.CallbackContext _)
        {
            if (Mode == CameraMode.FixedView) return;
            SetMode(Mode == CameraMode.ThirdPerson ? CameraMode.FirstPerson : CameraMode.ThirdPerson);
        }

        /// <summary>Pasa a una vista fija en primera persona situada en <paramref name="viewPoint"/>.</summary>
        public void EnterFixedView(Transform viewPoint)
        {
            if (Mode != CameraMode.FixedView)
                modeBeforeFixedView = Mode;
            fixedViewCamera.transform.SetPositionAndRotation(viewPoint.position, viewPoint.rotation);
            SetMode(CameraMode.FixedView);
        }

        /// <summary>Vuelve a la vista que había antes de EnterFixedView.</summary>
        public void ExitFixedView() => SetMode(modeBeforeFixedView);

        public void SetMode(CameraMode mode)
        {
            Mode = mode;
            bool thirdPerson = mode == CameraMode.ThirdPerson;
            bool firstPerson = mode == CameraMode.FirstPerson;
            bool fixedView = mode == CameraMode.FixedView;

            if (firstPerson)
            {
                // Empieza mirando hacia donde mira el jugador.
                firstPersonPanTilt.PanAxis.Value = playerMovement.transform.eulerAngles.y;
                firstPersonPanTilt.TiltAxis.Value = 0f;
            }

            thirdPersonCamera.Priority = thirdPerson ? ActivePriority : InactivePriority;
            firstPersonCamera.Priority = firstPerson ? ActivePriority : InactivePriority;
            fixedViewCamera.Priority = fixedView ? ActivePriority : InactivePriority;

            ApplyLookInput();

            playerMovement.enabled = thirdPerson;
            playerVisuals.SetActive(thirdPerson);
        }
    }
}
