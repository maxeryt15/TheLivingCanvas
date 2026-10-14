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
        [SerializeField] float fadeSeconds = 0.35f;
        [SerializeField] float holdSeconds = 0.1f;
        [Tooltip("Raiz del jugador (con CharacterController).")]
        [SerializeField] Transform player;
        [Tooltip("Mirada en primera persona; puede ser null.")]
        [SerializeField] CinemachinePanTilt panTilt;

        public bool Busy { get; private set; }

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
            yield return Fade(0f, 1f);

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
            yield return Fade(1f, 0f);
            Busy = false;
        }

        IEnumerator Fade(float from, float to)
        {
            if (fade == null) yield break;
            float t = 0f;
            float dur = Mathf.Max(0.0001f, fadeSeconds);
            while (t < dur)
            {
                t += Time.unscaledDeltaTime;
                fade.alpha = Mathf.Lerp(from, to, Mathf.Clamp01(t / dur));
                yield return null;
            }
            fade.alpha = to;
        }

        void SetInside(bool inside)
        {
            if (exteriorRoot != null) exteriorRoot.SetActive(!inside);
            if (interiorRoot != null) interiorRoot.SetActive(inside);
        }
    }
}
