using System.Collections;
using UnityEngine;
using UnityEngine.AI;

namespace TheLivingCanvas.Npcs
{
    /// <summary>
    /// Deja que un personaje pase entre el interior y el exterior del museo por las puertas. Solo el área donde está el jugador
    /// está activa (ver AreaTransition): al cruzar la puerta el personaje cambia de área y queda congelado hasta que el jugador vaya
    /// allí; entonces reaparece en una parada al azar de esa área. Cada área tiene su propia lista de paradas; las puertas aparecen
    /// varias veces para que a veces toque cruzar.
    /// </summary>
    [RequireComponent(typeof(NpcRoutine), typeof(NavMeshAgent))]
    public class NpcAreaTraveler : MonoBehaviour
    {
        [SerializeField] NpcRoutine routine;
        [SerializeField] GameObject interiorRoot;
        [SerializeField] GameObject exteriorRoot;
        [SerializeField] Transform[] interiorStops;
        [SerializeField] Transform[] exteriorStops;
        [SerializeField] Transform interiorDoor;
        [SerializeField] Transform exteriorDoor;
        [SerializeField] bool startsOutside;
        [Tooltip("Veces que aparece la puerta en la lista de paradas (más veces = sale/entra más a menudo).")]
        [SerializeField, Min(1)] int doorWeight = 4;

        NavMeshAgent agent;
        bool outside;
        bool scatterPending;

        void Awake()
        {
            agent = GetComponent<NavMeshAgent>();
            if (routine == null) routine = GetComponent<NpcRoutine>();
            outside = startsOutside;
            routine.SetStops(BuildStops(outside));
        }

        void OnEnable()
        {
            if (scatterPending) StartCoroutine(Scatter());
        }

        void Update()
        {
            if (!routine.Arrived) return;
            var door = outside ? exteriorDoor : interiorDoor;
            if (door != null && routine.CurrentStopPoint == door) Cross();
        }

        void Cross()
        {
            outside = !outside;
            routine.SetStops(BuildStops(outside));
            var spawn = outside ? exteriorDoor : interiorDoor;
            agent.enabled = false;
            if (spawn != null) transform.position = spawn.position;
            scatterPending = true;
            var root = outside ? exteriorRoot : interiorRoot;
            transform.SetParent(root.transform, true);
            // Si la otra área estuviera activa, OnEnable no se vuelve a llamar: reaparece aquí mismo.
            if (isActiveAndEnabled) StartCoroutine(Scatter());
        }

        IEnumerator Scatter()
        {
            yield return null;   // deja que el NavMeshSurface del área recién activada registre sus datos
            scatterPending = false;
            agent.enabled = true;
            routine.RestartAtRandomStop();
        }

        NpcStop[] BuildStops(bool forOutside)
        {
            var points = forOutside ? exteriorStops : interiorStops;
            var door = forOutside ? exteriorDoor : interiorDoor;
            var list = new System.Collections.Generic.List<NpcStop>();
            foreach (var p in points)
            {
                if (p == null) continue;
                list.Add(MakeStop(p));
            }
            if (door != null)
                for (int i = 0; i < doorWeight; i++) list.Add(new NpcStop { point = door, waitMin = 0f, waitMax = 0.3f, faceStopForward = false });
            return list.ToArray();
        }

        static NpcStop MakeStop(Transform p)
        {
            bool seat = p.Find("SeatPoint") != null;
            bool look = p.Find("LookTarget") != null;
            return new NpcStop
            {
                point = p,
                waitMin = seat ? 1f : look ? 60f : 3f,
                waitMax = seat ? 2f : look ? 120f : 9f,
                faceStopForward = look
            };
        }
    }
}
