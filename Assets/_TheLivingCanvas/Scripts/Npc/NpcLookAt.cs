using UnityEngine;

namespace TheLivingCanvas.Npcs
{
    /// <summary>
    /// Cuando la rutina espera en una parada que tiene un hijo "LookTarget" (p. ej. frente a una obra), gira el cuello y la cabeza
    /// hacia él (el cuerpo ya gira con faceStopForward). Se aplica en LateUpdate sobre la animación; sin objetivo, vuelve a la pose.
    /// </summary>
    [RequireComponent(typeof(Animator))]
    public class NpcLookAt : MonoBehaviour
    {
        [SerializeField] NpcRoutine routine;
        [SerializeField] float blendSeconds = 0.6f;
        [SerializeField, Range(10f, 90f)] float maxAngle = 70f;
        [SerializeField, Range(0f, 1f)] float headShare = 0.65f;

        /// <summary>Si no es null, tiene prioridad sobre el LookTarget de la parada (p. ej. la cámara del jugador al hablar).</summary>
        public Transform LookOverride { get; set; }

        Transform head, neck;
        float weight;
        Vector3 lastTarget;
        bool hasTarget;

        void Awake()
        {
            var animator = GetComponent<Animator>();
            head = animator.GetBoneTransform(HumanBodyBones.Head);
            neck = animator.GetBoneTransform(HumanBodyBones.Neck);
            if (routine == null) routine = GetComponent<NpcRoutine>();
        }

        void LateUpdate()
        {
            if (head == null) return;
            // Mientras charla con el jugador mira a sus ojos (LookOverride); si no, al LookTarget de la parada.
            Transform target = LookOverride;
            if (target == null)
            {
                Transform stop = routine != null && routine.Arrived ? routine.CurrentStopPoint : null;
                target = stop != null ? stop.Find("LookTarget") : null;
            }
            if (target != null) { lastTarget = target.position; hasTarget = true; }

            weight = Mathf.MoveTowards(weight, target != null ? 1f : 0f, Time.deltaTime / Mathf.Max(0.01f, blendSeconds));
            if (weight <= 0.001f || !hasTarget) return;

            Vector3 forward = transform.forward;
            Vector3 to = lastTarget - head.position;
            if (to.sqrMagnitude < 0.0001f) return;
            Vector3 desired = Vector3.RotateTowards(forward, to.normalized, maxAngle * Mathf.Deg2Rad, 0f);
            Quaternion delta = Quaternion.FromToRotation(forward, desired);

            if (neck != null) neck.rotation = Quaternion.Slerp(Quaternion.identity, delta, weight * (1f - headShare)) * neck.rotation;
            head.rotation = Quaternion.Slerp(Quaternion.identity, delta, weight * headShare) * head.rotation;
        }
    }
}
