using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace TheLivingCanvas.Npcs
{
    /// <summary>
    /// SOLO PARA PRUEBAS (quitar cuando termine la revision): los NPC se quedan quietos en su sitio y cada `secondsPerClip` pasan al
    /// siguiente clip de su lista (caminar masculino/femenino + poses de pie), para revisar visualmente que ninguna animacion se rompa.
    /// Anula la rutina y el agente mientras esta activo; el nombre del clip actual sale en pantalla.
    /// </summary>
    public class NpcAnimShowcase : MonoBehaviour
    {
        [System.Serializable]
        public class Entry
        {
            public Animator animator;
            public AnimationClip[] clips;
            [HideInInspector] public PlayableGraph graph;
            [HideInInspector] public AnimationPlayableOutput output;
        }

        public Entry[] entries;
        public float secondsPerClip = 10f;
        int index = -1;
        float next;
        string label = "";

        void Start()
        {
            foreach (var e in entries)
            {
                var routine = e.animator.GetComponent<NpcRoutine>(); if (routine != null) routine.enabled = false;
                var agent = e.animator.GetComponent<UnityEngine.AI.NavMeshAgent>(); if (agent != null) agent.enabled = false;
                e.animator.applyRootMotion = false; e.animator.speed = 1f;
                e.graph = PlayableGraph.Create("showcase_" + e.animator.name);
                e.graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
                e.output = AnimationPlayableOutput.Create(e.graph, "out", e.animator);
                e.graph.Play();
            }
            Advance();
        }

        void Update()
        {
            if (Time.time >= next) Advance();
        }

        void Advance()
        {
            index++;
            next = Time.time + secondsPerClip;
            int total = 0;
            foreach (var e in entries)
            {
                total = Mathf.Max(total, e.clips.Length);
                var clip = e.clips[index % e.clips.Length];
                var cp = AnimationClipPlayable.Create(e.graph, clip);
                cp.SetApplyFootIK(false);
                e.output.SetSourcePlayable(cp);
            }
            label = $"Clip {index % total + 1}/{total}: {entries[0].clips[index % entries[0].clips.Length].name}";
            Debug.Log($"[NpcAnimShowcase] {label}: " + string.Join(", ", System.Array.ConvertAll(entries, e => e.animator.name + "=" + e.clips[index % e.clips.Length].name)));
        }

        void OnGUI()
        {
            var style = new GUIStyle(GUI.skin.label) { fontSize = 20, fontStyle = FontStyle.Bold };
            style.normal.textColor = Color.white;
            GUI.Label(new Rect(20, 20, 900, 30), label + "  (cada " + secondsPerClip + " s)", style);
            int rem = Mathf.CeilToInt(next - Time.time);
            GUI.Label(new Rect(20, 50, 900, 30), "siguiente en " + rem + " s", style);
        }

        void OnDestroy()
        {
            if (entries == null) return;
            foreach (var e in entries) if (e.graph.IsValid()) e.graph.Destroy();
        }
    }
}
