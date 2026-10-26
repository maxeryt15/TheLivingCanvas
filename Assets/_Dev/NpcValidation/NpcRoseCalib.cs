using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

// Dev only (temporal): en Play prueba varios clips de sentado en Rose, mide cadera/pies y captura PNG. Sale de Play al terminar.
public class NpcRoseCalib : MonoBehaviour
{
    public GameObject exteriorRoot, interiorRoot, rose;
    public string outDir = "D:/TheLivingCanvas/ArtSource/_Exports/NPC_Validation/rose_seat";
    public string[] clipNames = { "Sit_Chair_Idle", "Rig|Sitting_Idle_Loop", "Sitting_Idle", "Rig|Sitting_Talking_Loop" };

#if UNITY_EDITOR
    IEnumerator Start()
    {
        Directory.CreateDirectory(outDir);
        yield return null;
        exteriorRoot.SetActive(false); interiorRoot.SetActive(true);
        foreach (var r in FindObjectsByType<NpcRoseCalib>(FindObjectsSortMode.None)) { }
        foreach (var cam0 in Camera.allCameras) cam0.enabled = false;
        var camGo = new GameObject("CalibCam"); var cam = camGo.AddComponent<Camera>(); cam.nearClipPlane = 0.05f;
        yield return new WaitForSeconds(0.5f);

        var clips = new System.Collections.Generic.Dictionary<string, AnimationClip>();
        foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:AnimationClip", new[] { "Assets/_TheLivingCanvas/Art/Animations" }))
            foreach (var o in UnityEditor.AssetDatabase.LoadAllAssetsAtPath(UnityEditor.AssetDatabase.GUIDToAssetPath(guid)))
            { var c = o as AnimationClip; if (c != null && System.Array.IndexOf(clipNames, c.name) >= 0 && !clips.ContainsKey(c.name)) clips[c.name] = c; }

        var an = rose.GetComponent<Animator>(); an.applyRootMotion = false;
        var floorY = rose.transform.position.y; var basePos = rose.transform.position;
        for (int i = 0; i < clipNames.Length; i++)
        {
            if (!clips.TryGetValue(clipNames[i], out var clip)) { Debug.Log("[RoseCalib] falta clip " + clipNames[i]); continue; }
            var g = PlayableGraph.Create("calib" + i); g.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
            var output = AnimationPlayableOutput.Create(g, "o", an); var p = AnimationClipPlayable.Create(g, clip); output.SetSourcePlayable(p); g.Play();
            yield return new WaitForSeconds(0.6f);
            Transform B(HumanBodyBones b) => an.GetBoneTransform(b);
            Debug.Log($"[RoseCalib] {clip.name}: hipsY {B(HumanBodyBones.Hips).position.y - floorY:0.000} hipsX {B(HumanBodyBones.Hips).position.x - basePos.x:0.000} lFootY {B(HumanBodyBones.LeftFoot).position.y - floorY:0.000} rFootY {B(HumanBodyBones.RightFoot).position.y - floorY:0.000} lKneeX {B(HumanBodyBones.LeftLowerLeg).position.x - basePos.x:0.000} lFootX {B(HumanBodyBones.LeftFoot).position.x - basePos.x:0.000}");
            var look = basePos + Vector3.up * 0.7f + Vector3.right * 0.1f;
            var views = new[] { new Vector3(-0.1f, 0.9f, -2.0f), new Vector3(-1.8f, 1.1f, -1.6f), new Vector3(1.6f, 1.2f, -1.8f) };
            for (int v = 0; v < views.Length; v++)
            {
                cam.transform.position = basePos + views[v]; cam.transform.LookAt(look); cam.fieldOfView = 40f;
                var rt = new RenderTexture(900, 700, 24); cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt;
                var tex = new Texture2D(900, 700, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 900, 700), 0, 0); tex.Apply();
                cam.targetTexture = null; RenderTexture.active = null;
                File.WriteAllBytes($"{outDir}/{i}_{clip.name.Replace("|", "_")}_v{v}.png", tex.EncodeToPNG()); Destroy(tex); rt.Release();
            }
            g.Destroy();
        }
        Debug.Log("[RoseCalib] listo");
        UnityEditor.EditorApplication.isPlaying = false;
    }
#endif
}
