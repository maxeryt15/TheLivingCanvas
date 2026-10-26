using UnityEngine;
using UnityEngine.AI;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Un punto de parada de la rutina: dónde ir, cuánto esperar y si mira hacia la orientación del punto.</summary>
    [System.Serializable]
    public struct NpcStop
    {
        public Transform point;
        [Min(0f)] public float waitMin;
        [Min(0f)] public float waitMax;
        [Tooltip("Al llegar, gira hasta la orientación (forward) del punto.")]
        public bool faceStopForward;
    }

    /// <summary>
    /// Rutina de un personaje sobre el NavMesh: recorre sus paradas (en orden o al azar), espera en cada una
    /// y se detiene mientras habla con el jugador. Con una sola parada se queda en su puesto.
    /// </summary>
    [RequireComponent(typeof(NavMeshAgent))]
    public class NpcRoutine : MonoBehaviour
    {
        [SerializeField] NpcStop[] stops;
        [SerializeField] bool randomOrder;
        [Tooltip("Opcional: se detiene mientras el jugador habla con este personaje.")]
        [SerializeField] Npc npc;
        [Tooltip("Opcional: recibe el parámetro float \"Speed\" (si el controller lo tiene).")]
        [SerializeField] Animator animator;
        [SerializeField] float turnSpeed = 360f;
        [SerializeField] float arriveDistance = 0.2f;
        [Tooltip("Velocidad (m/s) a la que el ciclo de caminar no patina; la animacion se acelera/frena segun la velocidad real del agente.")]
        [SerializeField] float walkRefSpeed = 1.08f;

        [Tooltip("Cada cuantos segundos (min, max) cambia de pose de espera mientras esta parado (IdleVariant 0..idleVariants-1).")]
        [SerializeField] Vector2 idleChangeSeconds = new Vector2(5f, 10f);
        [SerializeField] int idleVariants = 3;

        static readonly int SpeedHash = Animator.StringToHash("Speed");
        static readonly int IdleVariantHash = Animator.StringToHash("IdleVariant");
        bool hasIdleParam;
        float nextIdleChange;

        NavMeshAgent agent;
        bool hasSpeedParam;
        int index = -1;
        float waitUntil;
        bool arrived;

        /// <summary>true mientras espera en la parada actual (ya llegó).</summary>
        public bool Arrived => arrived;
        /// <summary>true: la rutina se detiene (p. ej. mientras el jugador charla con este personaje).</summary>
        public bool Hold { get; set; }
        /// <summary>Punto de la parada actual (o null si todavía no tiene).</summary>
        public Transform CurrentStopPoint => stops != null && index >= 0 && index < stops.Length ? stops[index].point : null;

        /// <summary>Cambia el conjunto de paradas (p. ej. al pasar de una zona del museo a otra) y reinicia el recorrido.</summary>
        public void SetStops(NpcStop[] newStops)
        {
            stops = newStops;
            index = -1;
            arrived = false;
        }

        /// <summary>Coloca al personaje en una parada al azar de su conjunto actual y sigue el recorrido desde ahí.</summary>
        public void RestartAtRandomStop()
        {
            if (stops == null || stops.Length == 0) return;
            var p = stops[Random.Range(0, stops.Length)].point;
            if (p != null && NavMesh.SamplePosition(p.position, out var hit, 2f, NavMesh.AllAreas)) agent.Warp(hit.position);
            index = -1;
            arrived = false;
            NextStop();
        }

        void Awake()
        {
            agent = GetComponent<NavMeshAgent>();
            if (animator != null)
                foreach (var p in animator.parameters)
                {
                    if (p.nameHash == SpeedHash) hasSpeedParam = true;
                    if (p.nameHash == IdleVariantHash) hasIdleParam = true;
                }
        }

        void Start()
        {
            if (stops == null || stops.Length == 0) return;
            // Si Start cae antes de que el NavMesh exista, el agente quedaría sin colocar.
            if (!agent.isOnNavMesh && NavMesh.SamplePosition(transform.position, out var hit, 2f, NavMesh.AllAreas))
                agent.Warp(hit.position);
            NextStop();
        }

        void Update()
        {
            if (animator != null)
            {
                float v = agent.velocity.magnitude;
                if (hasSpeedParam) animator.SetFloat(SpeedHash, v, 0.1f, Time.deltaTime);
                animator.speed = v > 0.1f ? Mathf.Clamp(v / walkRefSpeed, 0.75f, 1.35f) : 1f;   // pies sin patinar
            }

            if (stops == null || stops.Length == 0 || !agent.isOnNavMesh) return;

            // Conversación: quieto (la rotación hacia el jugador la hace Npc).
            bool talking = Hold || (npc != null && npc.InConversation);
            agent.isStopped = talking;
            if (talking) return;

            // Parado: cambia de pose de espera de vez en cuando (Idle_A / Idle_B / brazos cruzados).
            if (hasIdleParam && agent.velocity.sqrMagnitude < 0.01f && Time.time >= nextIdleChange)
            {
                animator.SetInteger(IdleVariantHash, Random.Range(0, Mathf.Max(1, idleVariants)));
                nextIdleChange = Time.time + Random.Range(idleChangeSeconds.x, idleChangeSeconds.y);
            }

            if (!arrived)
            {
                if (!agent.pathPending && agent.remainingDistance <= Mathf.Max(arriveDistance, agent.stoppingDistance))
                {
                    arrived = true;
                    waitUntil = Time.time + Random.Range(stops[index].waitMin, Mathf.Max(stops[index].waitMin, stops[index].waitMax));
                }
                return;
            }

            if (stops[index].faceStopForward && stops[index].point != null)
                FaceDirection(stops[index].point.forward);

            if (Time.time >= waitUntil && stops.Length > 1) NextStop();
        }

        void NextStop()
        {
            int next = index;
            if (randomOrder && stops.Length > 1)
                while (next == index) next = Random.Range(0, stops.Length);
            else
                next = (index + 1) % stops.Length;

            index = next;
            arrived = false;
            if (stops[index].point != null) agent.SetDestination(stops[index].point.position);
            else arrived = true;
        }

        void FaceDirection(Vector3 forward)
        {
            forward.y = 0f;
            if (forward.sqrMagnitude < 0.0001f) return;
            transform.rotation = Quaternion.RotateTowards(transform.rotation, Quaternion.LookRotation(forward), turnSpeed * Time.deltaTime);
        }
    }
}
