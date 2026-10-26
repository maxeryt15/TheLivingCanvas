using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Genera &lt;Npc&gt;_Walk.anim a partir de cada &lt;Npc&gt;_Idle.anim (la pose de reposo propia del avatar Humanoid
    /// más oscilaciones de músculos) y añade el estado Walk con el parámetro float "Speed" al AC_&lt;Npc&gt;.controller.
    /// </summary>
    public static class NpcWalkClipBuilder
    {
        const string NpcRoot = "Assets/_TheLivingCanvas/Art/Models/NPC";
        const float Duration = 1f;      // un ciclo completo = dos pasos
        const float Fps = 30f;

        // Amplitudes en unidades de músculo normalizado (-1..1).
        const float LegSwing = 0.36f;
        const float KneeBend = 0.45f;
        const float ArmSwing = 0.22f;
        const float TwistSwing = 0.05f;
        const float HipBob = 0.006f;    // RootT.y es altura de cadera normalizada
        public static float LegSign = -1f; // medido: con +1 el pie izquierdo iba hacia atrás en la fase 0..0.5

        [MenuItem("TheLivingCanvas/NPC/Build Walk Clips")]
        public static void BuildAll()
        {
            foreach (var idlePath in Directory.GetFiles(NpcRoot, "*_Idle.anim", SearchOption.AllDirectories))
            {
                var path = idlePath.Replace('\\', '/');
                Build(path);
            }
            AssetDatabase.SaveAssets();
        }

        public static void Build(string idlePath)
        {
            var idle = AssetDatabase.LoadAssetAtPath<AnimationClip>(idlePath);
            if (idle == null) return;
            string dir = Path.GetDirectoryName(idlePath).Replace('\\', '/');
            string name = Path.GetFileNameWithoutExtension(idlePath).Replace("_Idle", "");
            string walkPath = $"{dir}/{name}_Walk.anim";

            var walk = AssetDatabase.LoadAssetAtPath<AnimationClip>(walkPath);
            if (walk == null)
            {
                walk = new AnimationClip();
                AssetDatabase.CreateAsset(walk, walkPath);
            }
            else walk.ClearCurves();
            walk.frameRate = Fps;

            // Valor base de cada curva del idle (pose de reposo del avatar).
            var baseline = new Dictionary<string, float>();
            var bindings = AnimationUtility.GetCurveBindings(idle);
            foreach (var b in bindings)
                baseline[b.propertyName] = AnimationUtility.GetEditorCurve(idle, b)[0].value;

            foreach (var b in bindings)
            {
                float v0 = baseline[b.propertyName];
                AnimationCurve curve;
                if (TryDelta(b.propertyName, out var delta))
                {
                    int n = Mathf.RoundToInt(Duration * Fps);
                    var keys = new Keyframe[n + 1];
                    for (int i = 0; i <= n; i++)
                    {
                        float t = (float)i / n; // 0..1 = una vuelta de fase
                        keys[i] = new Keyframe(t * Duration, v0 + delta(t * Mathf.PI * 2f));
                    }
                    curve = new AnimationCurve(keys);
                    for (int i = 0; i < curve.length; i++) curve.SmoothTangents(i, 0f);
                }
                else
                {
                    curve = new AnimationCurve(new Keyframe(0f, v0), new Keyframe(Duration, v0));
                }
                AnimationUtility.SetEditorCurve(walk, b, curve);
            }

            var settings = AnimationUtility.GetAnimationClipSettings(idle);
            settings.loopTime = true;
            settings.startTime = 0f;
            settings.stopTime = Duration;
            AnimationUtility.SetAnimationClipSettings(walk, settings);
            EditorUtility.SetDirty(walk);

            AddWalkState(dir, name, walk);
        }

        /// <summary>Desplazamiento respecto al reposo en función de la fase (radianes) para ese músculo.</summary>
        static bool TryDelta(string muscle, out System.Func<float, float> f)
        {
            f = null;
            bool left = muscle.StartsWith("Left");
            float side = left ? 1f : -1f;   // la pierna derecha va en contrafase
            switch (muscle)
            {
                case "Left Upper Leg Front-Back":
                case "Right Upper Leg Front-Back":
                    f = ph => LegSign * LegSwing * side * Mathf.Sin(ph);
                    return true;
                case "Left Lower Leg Stretch":
                case "Right Lower Leg Stretch":
                    // Flexiona la rodilla (valor menor = más doblada) mientras la pierna avanza.
                    f = ph => -KneeBend * Mathf.Pow(Mathf.Max(0f, Mathf.Cos(ph + (left ? 0f : Mathf.PI))), 1.5f);
                    return true;
                case "Left Arm Front-Back":
                case "Right Arm Front-Back":
                    f = ph => ArmSwing * side * Mathf.Sin(ph);
                    return true;
                case "Spine Twist Left-Right":
                    f = ph => TwistSwing * Mathf.Sin(ph);
                    return true;
                case "RootT.y":
                    f = ph => -HipBob * Mathf.Abs(Mathf.Sin(ph)) + HipBob * 0.5f;
                    return true;
            }
            return false;
        }

        static void AddWalkState(string dir, string name, AnimationClip walk)
        {
            var ctrl = AssetDatabase.LoadAssetAtPath<AnimatorController>($"{dir}/AC_{name}.controller");
            if (ctrl == null) return;

            bool hasParam = false;
            foreach (var p in ctrl.parameters) if (p.name == "Speed") hasParam = true;
            if (!hasParam) ctrl.AddParameter("Speed", AnimatorControllerParameterType.Float);

            var sm = ctrl.layers[0].stateMachine;
            AnimatorState idleState = null, walkState = null;
            foreach (var cs in sm.states)
            {
                if (cs.state.name == "Idle") idleState = cs.state;
                if (cs.state.name == "Walk") walkState = cs.state;
            }
            if (idleState == null) return;
            if (walkState == null) walkState = sm.AddState("Walk", new Vector3(200, 100, 0));
            walkState.motion = walk;

            if (idleState.transitions.Length == 0)
            {
                var toWalk = idleState.AddTransition(walkState);
                toWalk.hasExitTime = false; toWalk.duration = 0.2f;
                toWalk.AddCondition(AnimatorConditionMode.Greater, 0.1f, "Speed");
            }
            if (walkState.transitions.Length == 0)
            {
                var toIdle = walkState.AddTransition(idleState);
                toIdle.hasExitTime = false; toIdle.duration = 0.2f;
                toIdle.AddCondition(AnimatorConditionMode.Less, 0.1f, "Speed");
            }
            EditorUtility.SetDirty(ctrl);
        }
    }
}
