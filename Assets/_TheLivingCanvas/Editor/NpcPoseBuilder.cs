using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Crea clips de pose Humanoid (bucle) resolviendo los brazos con IK de dos huesos sobre un avatar y convirtiendo el resultado a musculos.
    /// Pose_Thinking: mano derecha en el menton, brazo izquierdo cruzado bajo el codo.  Pose_Observing: manos juntas a la espalda.
    /// El resto del cuerpo viene de una animacion base (Idle_A de KayKit).
    /// </summary>
    public static class NpcPoseBuilder
    {
        const string OutDir = "Assets/_TheLivingCanvas/Art/Animations/Poses";

        public struct Arm { public Transform up, low, hand; }

        static Arm GetArm(Animator an, bool left) => new Arm
        {
            up = an.GetBoneTransform(left ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm),
            low = an.GetBoneTransform(left ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm),
            hand = an.GetBoneTransform(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand),
        };

        /// <summary>IK analitico de dos huesos: lleva la mano a `target` con el codo hacia `pole`.</summary>
        static void SolveArm(Arm a, Vector3 target, Vector3 pole)
        {
            Vector3 S = a.up.position, E = a.low.position, W = a.hand.position;
            float l1 = (E - S).magnitude, l2 = (W - E).magnitude;
            Vector3 toT = target - S; float d = Mathf.Clamp(toT.magnitude, Mathf.Abs(l1 - l2) + 0.01f, (l1 + l2) * 0.999f);
            Vector3 dir = toT.normalized;
            float aa = (l1 * l1 - l2 * l2 + d * d) / (2f * d); float h = Mathf.Sqrt(Mathf.Max(0f, l1 * l1 - aa * aa));
            Vector3 perp = Vector3.ProjectOnPlane(pole - S, dir).normalized;
            Vector3 newE = S + dir * aa + perp * h;
            a.up.rotation = Quaternion.FromToRotation(E - S, newE - S) * a.up.rotation;
            a.low.rotation = Quaternion.FromToRotation(a.hand.position - a.low.position, (S + dir * d) - a.low.position) * a.low.rotation;
        }

        static AnimationClip Base() => AssetDatabase.LoadAllAssetsAtPath("Assets/_TheLivingCanvas/Art/Animations/KayKit/KK_General.fbx")
            .OfType<AnimationClip>().FirstOrDefault(c => c.name.EndsWith("Idle_A"));

        static bool IsArmMuscle(string n) => (n.StartsWith("Left") || n.StartsWith("Right")) &&
            (n.Contains("Shoulder") || n.Contains("Arm") || n.Contains("Forearm") || n.Contains("Hand")) && !n.Contains("Thumb") && !n.Contains("Index") && !n.Contains("Middle") && !n.Contains("Ring") && !n.Contains("Little");

        /// <param name="rig">instancia Humanoid en escena (se restaura al final)</param>
        public static AnimationClip Build(string name, GameObject rig, System.Action<Animator, Arm, Arm> posing, Dictionary<string, float> extra)
        {
            var an = rig.GetComponent<Animator>(); bool was = an.enabled; an.enabled = false;
            var baseClip = Base();
            baseClip.SampleAnimation(rig, 0f);
            posing(an, GetArm(an, true), GetArm(an, false));
            var handler = new HumanPoseHandler(an.avatar, rig.transform);
            var pose = new HumanPose(); handler.GetHumanPose(ref pose); handler.Dispose();
            var solved = new Dictionary<string, float>();
            for (int i = 0; i < HumanTrait.MuscleCount; i++)
                if (IsArmMuscle(HumanTrait.MuscleName[i])) solved[HumanTrait.MuscleName[i]] = pose.muscles[i];
            if (extra != null) foreach (var kv in extra) solved[kv.Key] = kv.Value;
            baseClip.SampleAnimation(rig, 0f);
            an.enabled = was;

            Directory.CreateDirectory(OutDir);
            string path = $"{OutDir}/{name}.anim";
            var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
            if (clip == null) { clip = new AnimationClip(); AssetDatabase.CreateAsset(clip, path); } else clip.ClearCurves();
            clip.frameRate = 30f;
            float len = baseClip.length;
            foreach (var b in AnimationUtility.GetCurveBindings(baseClip))
            {
                var c = AnimationUtility.GetEditorCurve(baseClip, b);
                if (solved.TryGetValue(b.propertyName, out float v))
                    c = new AnimationCurve(new Keyframe(0f, v), new Keyframe(len, v));
                AnimationUtility.SetEditorCurve(clip, b, c);
            }
            foreach (var kv in solved)   // musculos que la base no animaba
            {
                var b = EditorCurveBinding.FloatCurve("", typeof(Animator), kv.Key);
                if (AnimationUtility.GetEditorCurve(clip, b) == null)
                    AnimationUtility.SetEditorCurve(clip, b, new AnimationCurve(new Keyframe(0f, kv.Value), new Keyframe(len, kv.Value)));
            }
            var s = AnimationUtility.GetAnimationClipSettings(baseClip); s.loopTime = true; s.stopTime = len;
            AnimationUtility.SetAnimationClipSettings(clip, s);
            EditorUtility.SetDirty(clip); AssetDatabase.SaveAssets();
            return clip;
        }

        /// <summary>Mano derecha al menton (codo apoyado en la mano izquierda), cabeza ligeramente ladeada.</summary>
        public static AnimationClip BuildThinking(GameObject rig)
        {
            return Build("Pose_Thinking", rig, (an, L, R) =>
            {
                var head = an.GetBoneTransform(HumanBodyBones.Head); var chest = an.GetBoneTransform(HumanBodyBones.UpperChest) ?? an.GetBoneTransform(HumanBodyBones.Chest);
                var root = rig.transform; Vector3 f = root.forward, r = root.right;
                Vector3 chin = head.position - Vector3.up * 0.11f + f * 0.10f;
                Vector3 elbowSupport = chest.position - Vector3.up * 0.20f + f * 0.14f - r * 0.02f;      // sobre la mano izquierda, delante del torso
                SolveArm(R, chin, R.up.position + Vector3.down * 0.5f - r * 0.2f + f * 0.2f);
                Vector3 leftHandT = chest.position - Vector3.up * 0.26f + f * 0.16f + r * 0.18f;           // mano izquierda bajo el codo derecho
                SolveArm(L, leftHandT, L.up.position + Vector3.down * 0.5f + r * 0.1f);
            }, new Dictionary<string, float> { { "Head Tilt Left-Right", 0.10f }, { "Neck Tilt Left-Right", 0.05f } });
        }

        /// <summary>Observando una obra: manos cogidas a la espalda.</summary>
        public static AnimationClip BuildObserving(GameObject rig)
        {
            return Build("Pose_Observing", rig, (an, L, R) =>
            {
                var hips = an.GetBoneTransform(HumanBodyBones.Hips); var root = rig.transform; Vector3 f = root.forward, r = root.right;
                Vector3 back = hips.position + Vector3.up * 0.10f - f * 0.16f;
                SolveArm(R, back + r * 0.04f, R.up.position + Vector3.down * 0.5f + r * 0.3f - f * 0.1f);
                SolveArm(L, back - r * 0.04f, L.up.position + Vector3.down * 0.5f - r * 0.3f - f * 0.1f);
            }, new Dictionary<string, float> { { "Head Nod Down-Up", -0.08f } });
        }

        // ------------------------------------------------------------------ poses estaticas de pie (referencias de postura: brazos cruzados, manos en la cadera, atras, delante...)
        public delegate void PoseFn(Animator an, Arm L, Arm R, Transform root, Vector3 f, Vector3 r);

        static Vector3 Hang(Arm a, float k = 0.97f) => a.up.position + Vector3.down * ((a.low.position - a.up.position).magnitude + (a.hand.position - a.low.position).magnitude) * k;

        public static readonly Dictionary<string, PoseFn> Poses = new Dictionary<string, PoseFn>
        {
            // manos en la cadera, codos hacia fuera
            { "Stand_HandsOnHips", (an, L, R, root, f, r) => {
                var h = an.GetBoneTransform(HumanBodyBones.Hips).position;
                SolveArm(R, h + r * 0.20f + Vector3.up * 0.05f + f * 0.02f, R.up.position + r * 0.6f - f * 0.15f);
                SolveArm(L, h - r * 0.20f + Vector3.up * 0.05f + f * 0.02f, L.up.position - r * 0.6f - f * 0.15f); } },
            // manos cogidas a la espalda
            { "Stand_HandsBehind", (an, L, R, root, f, r) => {
                var h = an.GetBoneTransform(HumanBodyBones.Hips).position + Vector3.up * 0.10f - f * 0.16f;
                SolveArm(R, h + r * 0.04f, R.up.position + Vector3.down * 0.5f + r * 0.3f - f * 0.1f);
                SolveArm(L, h - r * 0.04f, L.up.position + Vector3.down * 0.5f - r * 0.3f - f * 0.1f); } },
            // una mano en la cadera, el otro brazo relajado
            { "Stand_OneHipRight", (an, L, R, root, f, r) => {
                var h = an.GetBoneTransform(HumanBodyBones.Hips).position;
                SolveArm(R, h + r * 0.20f + Vector3.up * 0.05f + f * 0.02f, R.up.position + r * 0.6f - f * 0.15f);
                SolveArm(L, Hang(L) + f * 0.03f - r * 0.04f, L.up.position - Vector3.up * 0.5f - r * 0.2f); } },
            { "Stand_OneHipLeft", (an, L, R, root, f, r) => {
                var h = an.GetBoneTransform(HumanBodyBones.Hips).position;
                SolveArm(L, h - r * 0.20f + Vector3.up * 0.05f + f * 0.02f, L.up.position - r * 0.6f - f * 0.15f);
                SolveArm(R, Hang(R) + f * 0.03f + r * 0.04f, R.up.position - Vector3.up * 0.5f + r * 0.2f); } },
            // relajado: brazos caidos con las manos algo adelantadas
            { "Stand_Relaxed", (an, L, R, root, f, r) => {
                SolveArm(R, Hang(R, 0.93f) + f * 0.06f + r * 0.03f, R.up.position - Vector3.up * 0.5f + r * 0.2f);
                SolveArm(L, Hang(L, 0.93f) + f * 0.06f - r * 0.03f, L.up.position - Vector3.up * 0.5f - r * 0.2f); } },
        };

        /// <param name="shift">desplazamiento de peso: spine/cabeza/rodilla (valores en unidades de musculo sobre la base)</param>
        public static AnimationClip BuildStand(string name, GameObject rig, PoseFn fn, Dictionary<string, float> delta, float armOut = 0f, float elbowOut = 0f)
        {
            var an = rig.GetComponent<Animator>(); bool was = an.enabled; an.enabled = false;
            var baseClip = Base(); baseClip.SampleAnimation(rig, 0f);
            var toes = an.GetBoneTransform(HumanBodyBones.LeftToes); var foot = an.GetBoneTransform(HumanBodyBones.LeftFoot);
            Vector3 f = Vector3.ProjectOnPlane(toes.position - foot.position, Vector3.up); if (f.sqrMagnitude < 1e-6f) f = rig.transform.forward; f.Normalize();
            Vector3 r = Vector3.Cross(Vector3.up, f);
            fn(an, GetArm(an, true), GetArm(an, false), rig.transform, f, r);
            var handler = new HumanPoseHandler(an.avatar, rig.transform); var pose = new HumanPose(); handler.GetHumanPose(ref pose); handler.Dispose();
            var solved = new Dictionary<string, float>();
            for (int i = 0; i < HumanTrait.MuscleCount; i++) if (IsArmMuscle(HumanTrait.MuscleName[i])) solved[HumanTrait.MuscleName[i]] = pose.muscles[i];
            if (armOut != 0f) { foreach (var side in new[] { "Left", "Right" }) { if (solved.ContainsKey(side + " Arm Down-Up")) solved[side + " Arm Down-Up"] += armOut; } }
            if (elbowOut != 0f) { foreach (var side in new[] { "Left", "Right" }) { if (solved.ContainsKey(side + " Forearm Stretch")) solved[side + " Forearm Stretch"] += elbowOut; } }
            if (delta != null) foreach (var kv in delta) if (solved.ContainsKey(kv.Key)) solved[kv.Key] += kv.Value;   // deltas sobre musculos de brazo (p. ej. hombro)
            baseClip.SampleAnimation(rig, 0f); an.enabled = was;

            Directory.CreateDirectory(OutDir);
            string path = $"{OutDir}/{name}.anim";
            var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
            if (clip == null) { clip = new AnimationClip(); AssetDatabase.CreateAsset(clip, path); } else clip.ClearCurves();
            clip.frameRate = 30f; const float len = 4f;
            foreach (var b in AnimationUtility.GetCurveBindings(baseClip))
            {
                string pn = b.propertyName; var bc = AnimationUtility.GetEditorCurve(baseClip, b);
                float v0 = bc.Evaluate(0f);
                if (solved.TryGetValue(pn, out float sv)) v0 = sv;
                else if (delta != null && delta.TryGetValue(pn, out float d)) v0 += d;
                AnimationCurve c;
                if (pn == "Chest Front-Back" || pn == "Spine Front-Back" || pn == "UpperChest Front-Back")   // respiracion suave
                {
                    var keys = new Keyframe[9]; float a = pn.StartsWith("Spine") ? 0.012f : 0.018f;
                    for (int k = 0; k < 9; k++) keys[k] = new Keyframe(len * k / 8f, v0 + a * Mathf.Sin(k / 8f * Mathf.PI * 2f));
                    c = new AnimationCurve(keys); for (int k = 0; k < c.length; k++) c.SmoothTangents(k, 0f);
                }
                else c = new AnimationCurve(new Keyframe(0f, v0), new Keyframe(len, v0));
                AnimationUtility.SetEditorCurve(clip, b, c);
            }
            var s = AnimationUtility.GetAnimationClipSettings(baseClip); s.loopTime = true; s.startTime = 0f; s.stopTime = len;
            AnimationUtility.SetAnimationClipSettings(clip, s);
            EditorUtility.SetDirty(clip); AssetDatabase.SaveAssets();
            return clip;
        }
    }
}
