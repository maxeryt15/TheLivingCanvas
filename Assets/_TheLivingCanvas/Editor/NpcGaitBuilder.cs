using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Deriva dos caminares del ciclo del pack UAL (Walk_Loop / Walk_Formal_Loop) editando sus curvas musculares Humanoid:
    /// Male = erguido y seguro (zancada larga, hombros firmes, cadera casi quieta, braceo amplio);
    /// Female = mas femenino (zancada algo mas corta, pies mas cerca de la linea central, cadera y torso con mas balanceo, braceo suave).
    /// </summary>
    public static class NpcGaitBuilder
    {
        public const string OutDir = "Assets/_TheLivingCanvas/Art/Animations/Gait";
        const string UalPath = "Assets/_TheLivingCanvas/Art/Animations/UAL/UAL_Standard.fbx";

        public struct Gait
        {
            public string name, baseClip;
            public float leg, arm, hipSway, hipYaw, hipRoll, twist, chestSway;   // multiplicadores de la desviacion respecto a la media
            public float chestLean;     // desplazamiento de columna/pecho (musculo)
            public float legInOut;      // desplazamiento de "Upper Leg In-Out" (positivo = ver Measure)
            public float footLift;      // multiplicador de la elevacion del pie (Foot Up-Down)
            public float armOut;        // desplazamiento de 'Arm Down-Up' (separa los brazos del cuerpo; evita que las manos atraviesen la ropa)
        }

        public static AnimationClip Find(string name)
        {
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(UalPath))
            {
                var c = o as AnimationClip;
                if (c != null && c.name == name) return c;
            }
            return null;
        }

        static float Mean(AnimationCurve c, float len)
        {
            float s = 0; int n = 60;
            for (int i = 0; i < n; i++) s += c.Evaluate(len * i / n);
            return s / n;
        }

        public static AnimationClip Build(Gait g)
        {
            var src = Find(g.baseClip);
            Directory.CreateDirectory(OutDir);
            string path = $"{OutDir}/{g.name}.anim";
            var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
            if (clip == null) { clip = new AnimationClip(); AssetDatabase.CreateAsset(clip, path); }
            else clip.ClearCurves();
            clip.frameRate = 30f;
            float len = src.length;
            int n = Mathf.RoundToInt(len * 30f);

            var bindings = AnimationUtility.GetCurveBindings(src);
            var curves = new Dictionary<string, AnimationCurve>();
            foreach (var b in bindings) curves[b.propertyName] = AnimationUtility.GetEditorCurve(src, b);

            foreach (var b in bindings)
            {
                string p = b.propertyName;
                var c = curves[p];
                float mean = Mean(c, len);
                var keys = new Keyframe[n + 1];
                for (int i = 0; i <= n; i++)
                {
                    float t = len * i / n;
                    float v = c.Evaluate(t);
                    float dev = v - mean;
                    float outv = v;
                    if (p == "Left Upper Leg Front-Back" || p == "Right Upper Leg Front-Back") outv = mean + dev * g.leg;
                    else if (p == "Left Arm Front-Back" || p == "Right Arm Front-Back") outv = mean + dev * g.arm;
                    else if (p == "RootT.x") outv = mean + dev * g.hipSway;
                    else if (p == "RootQ.y") outv = mean + dev * g.hipYaw;
                    else if (p == "RootQ.z") outv = mean + dev * g.hipRoll;
                    else if (p.EndsWith("Twist Left-Right") && (p.StartsWith("Spine") || p.StartsWith("Chest") || p.StartsWith("UpperChest"))) outv = mean + dev * g.twist;
                    else if ((p == "UpperChest Left-Right" || p == "Chest Left-Right" || p == "Spine Left-Right")) outv = mean + dev * g.chestSway;
                    else if (p == "Spine Front-Back" || p == "Chest Front-Back" || p == "UpperChest Front-Back") outv = v + g.chestLean;
                    else if (p == "Left Upper Leg In-Out") outv = v + g.legInOut;
                    else if (p == "Right Upper Leg In-Out") outv = v - g.legInOut;
                    else if (p == "Left Arm Down-Up" || p == "Right Arm Down-Up") outv = v + g.armOut;
                    else if (p == "Left Foot Up-Down" || p == "Right Foot Up-Down") outv = mean + dev * g.footLift;
                    keys[i] = new Keyframe(t, outv);
                }
                keys[n].value = keys[0].value;   // cierre del bucle
                var nc = new AnimationCurve(keys);
                for (int i = 0; i < nc.length; i++) nc.SmoothTangents(i, 0f);
                AnimationUtility.SetEditorCurve(clip, b, nc);
            }
            // los cuaterniones de la raiz se renormalizan para que sigan siendo unitarios
            var qb = new Dictionary<string, EditorCurveBinding>();
            foreach (var b in AnimationUtility.GetCurveBindings(clip)) if (b.propertyName.StartsWith("RootQ.")) qb[b.propertyName] = b;
            if (qb.Count == 4)
            {
                var cx = AnimationUtility.GetEditorCurve(clip, qb["RootQ.x"]); var cy = AnimationUtility.GetEditorCurve(clip, qb["RootQ.y"]);
                var cz = AnimationUtility.GetEditorCurve(clip, qb["RootQ.z"]); var cw = AnimationUtility.GetEditorCurve(clip, qb["RootQ.w"]);
                for (int i = 0; i < cw.length; i++)
                {
                    float t = cw[i].time;
                    var q = new Quaternion(cx.Evaluate(t), cy.Evaluate(t), cz.Evaluate(t), cw[i].value);
                    float m = Mathf.Sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w);
                    var k = cw[i]; k.value = q.w / m; cw.MoveKey(i, k);
                }
                AnimationUtility.SetEditorCurve(clip, qb["RootQ.w"], cw);
            }

            var settings = AnimationUtility.GetAnimationClipSettings(src);
            settings.loopTime = true; settings.loopBlend = false;
            settings.startTime = 0f; settings.stopTime = len;
            AnimationUtility.SetAnimationClipSettings(clip, settings);
            EditorUtility.SetDirty(clip);
            AssetDatabase.SaveAssets();
            return clip;
        }

        /// <summary>Mide el caminar sobre una instancia Humanoid: zancada, ancho de paso, braceo, giro de cadera/hombros, balanceo lateral e inclinacion del torso.</summary>
        public static string Measure(GameObject npc, AnimationClip clip)
        {
            var an = npc.GetComponent<Animator>();
            bool was = an.enabled; an.enabled = false;
            var lf = an.GetBoneTransform(HumanBodyBones.LeftFoot); var rf = an.GetBoneTransform(HumanBodyBones.RightFoot);
            var lu = an.GetBoneTransform(HumanBodyBones.LeftUpperLeg); var ru = an.GetBoneTransform(HumanBodyBones.RightUpperLeg);
            var la = an.GetBoneTransform(HumanBodyBones.LeftUpperArm); var ra = an.GetBoneTransform(HumanBodyBones.RightUpperArm);
            var lh = an.GetBoneTransform(HumanBodyBones.LeftHand); var hips = an.GetBoneTransform(HumanBodyBones.Hips);
            var head = an.GetBoneTransform(HumanBodyBones.Head);
            int N = 40; float zmin = 9, zmax = -9, hipYmin = 9, hipYmax = -9, shMin = 999, shMax = -999, hpMin = 999, hpMax = -999, armMin = 9, armMax = -9, xsw = 0, lean = 0, fy = 0, fymax = -9;
            for (int i = 0; i < N; i++)
            {
                clip.SampleAnimation(npc, clip.length * i / N);
                Vector3 L = npc.transform.InverseTransformPoint(lf.position), R = npc.transform.InverseTransformPoint(rf.position);
                zmin = Mathf.Min(zmin, L.z); zmax = Mathf.Max(zmax, L.z); xsw += Mathf.Abs(L.x - R.x);
                Vector3 hv = npc.transform.InverseTransformPoint(ru.position) - npc.transform.InverseTransformPoint(lu.position);
                float hy = Mathf.Atan2(hv.z, hv.x) * Mathf.Rad2Deg; hpMin = Mathf.Min(hpMin, hy); hpMax = Mathf.Max(hpMax, hy);
                Vector3 sv = npc.transform.InverseTransformPoint(ra.position) - npc.transform.InverseTransformPoint(la.position);
                float sy = Mathf.Atan2(sv.z, sv.x) * Mathf.Rad2Deg; shMin = Mathf.Min(shMin, sy); shMax = Mathf.Max(shMax, sy);
                float arm = npc.transform.InverseTransformPoint(lh.position).z - npc.transform.InverseTransformPoint(la.position).z; armMin = Mathf.Min(armMin, arm); armMax = Mathf.Max(armMax, arm);
                float hx = npc.transform.InverseTransformPoint(hips.position).x; hipYmin = Mathf.Min(hipYmin, hx); hipYmax = Mathf.Max(hipYmax, hx);
                lean += npc.transform.InverseTransformPoint(head.position).z - npc.transform.InverseTransformPoint(hips.position).z;
                fymax = Mathf.Max(fymax, L.y);
            }
            an.enabled = was;
            return $"stride(footZ)={(zmax - zmin):F2} stepWidth={(xsw / N):F2} handSwing={(armMax - armMin):F2} hipYaw={(hpMax - hpMin):F1}deg shoulderYaw={(shMax - shMin):F1}deg hipSway={(hipYmax - hipYmin):F3}m headLean={(lean / N):F3} footLift={fymax:F2}";
        }
    }
}
