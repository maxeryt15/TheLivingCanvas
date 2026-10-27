using System.Collections;
using Unity.Cinemachine;
using TheLivingCanvas.Player;
using UnityEngine;

namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Dueno de las dos areas del museo (exterior e interior). Solo esta activa el area donde esta el jugador:
    /// la otra (mallas, luces, sol) no cuesta nada. El interior vive bajo el mapa.
    /// Viajar = fundido a negro, mover al jugador, cambiar el area activa y fundido de vuelta.
    /// </summary>
    public class AreaTransition : MonoBehaviour
    {
        [SerializeField] GameObject exteriorRoot;
        [SerializeField] GameObject interiorRoot;
        [SerializeField] bool startInside;
        [SerializeField] CanvasGroup fade;
        [Tooltip("Cómo se cubre la pantalla al viajar entre áreas.")]
        [SerializeField] TheLivingCanvas.Ui.ScreenTransition.Kind transitionKind = TheLivingCanvas.Ui.ScreenTransition.Kind.Brush;
        [Tooltip("Si está activo, cada viaje usa el siguiente tipo (pincelada, tinta, disolución) en vez de siempre el mismo.")]
        [SerializeField] bool cycleKinds = true;
        [SerializeField] float coverSeconds = 0.6f;
        [SerializeField] float uncoverSeconds = 0.8f;
        [SerializeField] float holdSeconds = 0.1f;
        [Tooltip("Raiz del jugador (con CharacterController).")]
        [SerializeField] Transform player;
        [Tooltip("Mirada en primera persona; puede ser null.")]
        [SerializeField] CinemachinePanTilt panTilt;

        public bool Busy { get; private set; }
        static int travelCount;

        void Awake()
        {
            SetInside(startInside);
            if (fade != null) fade.alpha = 0f;
        }

        public void Travel(Transform destination, bool toInside)
        {
            if (Busy || destination == null || player == null) return;
            StartCoroutine(TravelRoutine(destination, toInside));
        }

        IEnumerator TravelRoutine(Transform destination, bool toInside)
        {
            Busy = true;
            var kind = transitionKind;
            if (cycleKinds)
            {
                var order = new[] { TheLivingCanvas.Ui.ScreenTransition.Kind.Brush, TheLivingCanvas.Ui.ScreenTransition.Kind.Ink, TheLivingCanvas.Ui.ScreenTransition.Kind.Dissolve };
                kind = order[travelCount++ % order.Length];
            }
            yield return TheLivingCanvas.Ui.ScreenTransition.Cover(kind, coverSeconds);

            var movement = player.GetComponent<PlayerMovement>();
            var controller = player.GetComponent<CharacterController>();
            if (movement != null) movement.enabled = false;
            if (controller != null) controller.enabled = false;

            float yaw = destination.eulerAngles.y;
            Vector3 delta = destination.position - player.position;
            player.SetPositionAndRotation(destination.position, Quaternion.Euler(0f, yaw, 0f));
            Physics.SyncTransforms();
            if (panTilt != null)
            {
                panTilt.PanAxis.Value = yaw;
                panTilt.TiltAxis.Value = 0f;
            }
            CinemachineCore.OnTargetObjectWarped(player, delta);

            // El area que se abandona se desactiva DESPUES de mover al jugador: asi nunca cae al vacio
            SetInside(toInside);

            if (controller != null) controller.enabled = true;
            if (movement != null) movement.enabled = true;

            if (holdSeconds > 0f) yield return new WaitForSecondsRealtime(holdSeconds);
            yield return TheLivingCanvas.Ui.ScreenTransition.Uncover(uncoverSeconds);
            Busy = false;
            TheLivingCanvas.Ui.Notifications.Show(toInside ? "You step into the museum" : "You step out into the gardens");
        }

        void SetInside(bool inside)
        {
            if (exteriorRoot != null) exteriorRoot.SetActive(!inside);
            if (interiorRoot != null) interiorRoot.SetActive(inside);
        }
    }
}
