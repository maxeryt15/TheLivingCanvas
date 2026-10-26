using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.AI;
using UnityEngine.Playables;

namespace TheLivingCanvas.Npcs
{
    /// <summary>
    /// Si la parada actual tiene un hijo "SeatPoint" (un banco), el personaje se sienta ahí un rato (animación sentado) y luego se
    /// levanta y sigue su recorrido. Mientras está sentado el NavMeshAgent queda apagado, así que la rutina espera.
    /// </summary>
    [RequireComponent(typeof(NpcRoutine), typeof(NavMeshAgent), typeof(Animator))]
    public class NpcSit : MonoBehaviour
    {
        [SerializeField] NpcRoutine routine;
        [SerializeField] AnimationClip sitClip;
        [SerializeField] Vector2 sitSeconds = new Vector2(20f, 45f);
        [SerializeField] float moveSeconds = 0.7f;

        NavMeshAgent agent;
        Animator animator;
        PlayableGraph graph;
        bool sitting, handled;
        float timer, moveT;
        Vector3 fromPos, toPos, standPos;
        Quaternion fromRot, toRot, standRot;

        void Awake()
        {
            agent = GetComponent<NavMeshAgent>();
            animator = GetComponent<Animator>();
            if (routine == null) routine = GetComponent<NpcRoutine>();
        }

        void Update()
        {
            if (sitting) { UpdateSitting(); return; }
            if (!routine.Arrived) { handled = false; return; }
            if (handled || sitClip == null) return;
            var stop = routine.CurrentStopPoint;
            var seat = stop != null ? stop.Find("SeatPoint") : null;
            if (seat != null) BeginSit(seat);
        }

        void BeginSit(Transform seat)
        {
            handled = true;
            standPos = transform.position; standRot = transform.rotation;
            fromPos = standPos; fromRot = standRot; toPos = seat.position; toRot = seat.rotation;
            agent.enabled = false;
            graph = PlayableGraph.Create("sit_" + name);
            graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
            var output = AnimationPlayableOutput.Create(graph, "out", animator);
            var clip = AnimationClipPlayable.Create(graph, sitClip);
            output.SetSourcePlayable(clip);
            graph.Play();
            sitting = true; moveT = 0f; timer = Random.Range(sitSeconds.x, sitSeconds.y);
        }

        void UpdateSitting()
        {
            if (moveT < 1f)
            {
                moveT = Mathf.Min(1f, moveT + Time.deltaTime / Mathf.Max(0.01f, moveSeconds));
                transform.SetPositionAndRotation(Vector3.Lerp(fromPos, toPos, moveT), Quaternion.Slerp(fromRot, toRot, moveT));
                return;
            }
            timer -= Time.deltaTime;
            if (timer <= 0f) StandUp();
        }

        void StandUp()
        {
            if (graph.IsValid()) graph.Destroy();
            transform.SetPositionAndRotation(standPos, standRot);
            agent.enabled = true;
            agent.Warp(standPos);
            sitting = false;
        }

        void OnDestroy()
        {
            if (graph.IsValid()) graph.Destroy();
        }
    }
}
