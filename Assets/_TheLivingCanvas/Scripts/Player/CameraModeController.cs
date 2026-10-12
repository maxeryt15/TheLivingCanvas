using TheLivingCanvas.Save;
using Unity.Cinemachine;
using UnityEngine;

namespace TheLivingCanvas.Player
{
    public enum CameraMode
    {
        FirstPerson,
        /// <summary>Primera persona fija en un punto (ej. frente al lienzo al pintar).</summary>
        FixedView
    }

    /// <summary>
    /// Cámara en primera persona (el juego no tiene tercera persona). Cambia la prioridad entre
    /// la cámara de los ojos y una vista fija para acciones puntuales (pintar), gira el cuerpo
    /// con la mirada y deja quieto al jugador mientras está en la vista fija.
    /// </summary>
    public class CameraModeController : MonoBehaviour, ISaveable
    {
        const int ActivePriority = 10;
        const int InactivePriority = 0;

        [SerializeField] CinemachineCamera firstPersonCamera;
        [Tooltip("Cámara sin movimiento propio; se coloca en el punto de vista pedido.")]
        [SerializeField] CinemachineCamera fixedViewCamera;
        [SerializeField] PlayerMovement playerMovement;
        [Tooltip("Cuerpo del jugador; siempre oculto para que no tape la vista.")]
        [SerializeField] GameObject playerVisuals;

        CinemachineInputAxisController firstPersonInput;
        CinemachinePanTilt firstPersonPanTilt;
        bool lookInputEnabled = true;

        public CameraMode Mode { get; private set; }

        /// <summary>Permite apagar el mirar con ratón/stick (ej. con el inventario abierto para usar el cursor).</summary>
        public void SetLookInputEnabled(bool enabled)
        {
            lookInputEnabled = enabled;
            ApplyLookInput();
        }

        void ApplyLookInput() =>
            firstPersonInput.enabled = Mode == CameraMode.FirstPerson && lookInputEnabled;

        void Awake()
        {
            firstPersonInput = firstPersonCamera.GetComponent<CinemachineInputAxisController>();
            firstPersonPanTilt = firstPersonCamera.GetComponent<CinemachinePanTilt>();
        }

        void Start()
        {
            LookAlongPlayer();
            SetMode(CameraMode.FirstPerson);
        }

        void Update()
        {
            // El cuerpo mira hacia donde mira la cámara: así el interactor y el movimiento usan la misma dirección.
            if (Mode == CameraMode.FirstPerson)
                playerMovement.transform.rotation = Quaternion.Euler(0f, firstPersonPanTilt.PanAxis.Value, 0f);
        }

        /// <summary>Pasa a una vista fija en primera persona situada en <paramref name="viewPoint"/>.</summary>
        public void EnterFixedView(Transform viewPoint)
        {
            fixedViewCamera.transform.SetPositionAndRotation(viewPoint.position, viewPoint.rotation);
            SetMode(CameraMode.FixedView);
        }

        /// <summary>Vuelve a la vista de los ojos, mirando hacia donde se quedó.</summary>
        public void ExitFixedView() => SetMode(CameraMode.FirstPerson);

        public void SetMode(CameraMode mode)
        {
            Mode = mode;
            bool firstPerson = mode == CameraMode.FirstPerson;

            firstPersonCamera.Priority = firstPerson ? ActivePriority : InactivePriority;
            fixedViewCamera.Priority = firstPerson ? InactivePriority : ActivePriority;

            ApplyLookInput();

            playerMovement.enabled = firstPerson;
            playerVisuals.SetActive(false);
        }

        void LookAlongPlayer()
        {
            firstPersonPanTilt.PanAxis.Value = playerMovement.transform.eulerAngles.y;
            firstPersonPanTilt.TiltAxis.Value = 0f;
        }

        // La orientación la guarda PlayerMovement (playerYaw); aquí solo se alinea la mirada al cargar.
        public void WriteSave(SaveData data) { }

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            firstPersonPanTilt.PanAxis.Value = data.playerYaw;
            firstPersonPanTilt.TiltAxis.Value = 0f;
        }
    }
}
