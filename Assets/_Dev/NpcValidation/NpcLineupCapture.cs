using System.Collections;
using System.IO;
using UnityEngine;

// Dev only: en Play captura a NPCs caminando desde varios angulos, guarda PNG y sale de Play.
public class NpcLineupCapture : MonoBehaviour
{
    public string[] npcs = { "Docent", "Guard", "Gentleman" };
    public string outDir = "D:/TheLivingCanvas/ArtSource/_Exports/NPC_Validation/torso_backing/play";
    public bool exitPlay = true;

    IEnumerator Start()
    {
        Directory.CreateDirectory(outDir);
        yield return new WaitForSeconds(1.0f);
        var camGo = new GameObject("CaptureCam"); var cam = camGo.AddComponent<Camera>(); cam.clearFlags = CameraClearFlags.Skybox;
        foreach (var main in Camera.allCameras) if (main != cam) main.enabled = false;
        var root = GameObject.Find("NPC_Lineup").transform;
        // (altura, distancia, fov, altura del objetivo)
        var views = new[] { new Vector4(2.3f, 1.3f, 30f, 1.4f), new Vector4(1.9f, 0.9f, 40f, 1.4f), new Vector4(1.0f, 2.2f, 35f, 0.9f) };
        for (int t = 0; t < 4; t++)
        {
            foreach (var n in npcs)
            {
                var tr = root.Find(n); if (tr == null) continue;
                for (int v = 0; v < views.Length; v++)
                {
                    var w = views[v];
                    cam.transform.position = new Vector3(tr.position.x, w.x, tr.position.z + w.y);
                    cam.transform.LookAt(tr.position + Vector3.up * w.w); cam.fieldOfView = w.z;
                    var rt = new RenderTexture(900, 700, 24); cam.targetTexture = rt; cam.Render();
                    RenderTexture.active = rt; var tex = new Texture2D(900, 700, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 900, 700), 0, 0); tex.Apply();
                    cam.targetTexture = null; RenderTexture.active = null;
                    File.WriteAllBytes($"{outDir}/{n}_t{t}_v{v}.png", tex.EncodeToPNG()); Destroy(tex); rt.Release();
                }
            }
            yield return new WaitForSeconds(0.3f);
        }
        Debug.Log("[NpcLineupCapture] listo: " + outDir);
#if UNITY_EDITOR
        if (exitPlay) UnityEditor.EditorApplication.isPlaying = false;
#endif
    }
}
