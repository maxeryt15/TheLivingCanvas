using UnityEngine;

/// <summary>PILOTO (aislado, no es produccion): blink automatico, expresiones por IMGUI, y mirada limitada de eye_L/eye_R.
/// Mirada: horizontal = eje local Z del hueso, vertical = eje local X (medido en Unity), limites +-20 / +-12 grados.</summary>
public class NpcFacePilotDemo : MonoBehaviour
{
    public Transform gazeTarget;
    public Animator animator;
    public string[] clips = { "Idle", "Breathing_Idle", "Walking", "Sitting_Idle", "Sit_To_Stand", "Stand_To_Sit", "Plant_A_Plant", "Pick_Fruit", "Look_Around", "Talking" };
    public float maxYaw = 20f, maxPitch = 12f, gazeSpeed = 12f;
    public bool gazeOn = true, autoBlink = true, talking;

    static readonly string[] Shapes = { "blink", "mouth_open", "mouth_smile", "mouth_frown", "mouth_round", "mouth_wide", "brow_raise", "brow_lower", "brow_worry" };
    SkinnedMeshRenderer smr;
    Transform head, eyeL, eyeR, root;
    Quaternion restL, restR, headRestRel;
    float[] manual = new float[9];
    float nextBlink = 2f, blinkT = -1f, yaw, pitch;
    Vector2 scroll;
    static int uiSlot;
    static bool panelsVisible = true, mouseGaze = true;
    static Camera cam;
    static float zoom;
    static Vector3 focus = new Vector3(0f, 1.3f, 0f);
    static float focusDist = 3.6f, focusFov = 40f;
    int slot;

    void Start()
    {
        smr = GetComponentInChildren<SkinnedMeshRenderer>();
        foreach (var t in GetComponentsInChildren<Transform>(true))
        {
            if (t.name == "head") head = t;
            else if (t.name == "eye_L") eyeL = t;
            else if (t.name == "eye_R") eyeR = t;
        }
        root = transform;
        restL = eyeL.localRotation; restR = eyeR.localRotation;
        headRestRel = Quaternion.Inverse(root.rotation) * head.rotation;
        slot = uiSlot++;
        if (animator == null) animator = GetComponent<Animator>();
        if (animator != null && animator.runtimeAnimatorController != null) animator.Play("Idle");
    }

    void LateUpdate()
    {
        // --- blend shapes (despues del Animator)
        float blink = manual[0];
        if (autoBlink)
        {
            nextBlink -= Time.deltaTime;
            if (nextBlink <= 0f && blinkT < 0f) blinkT = 0f;
            if (blinkT >= 0f)
            {
                blinkT += Time.deltaTime;
                blink = Mathf.Max(blink, Mathf.Sin(Mathf.Clamp01(blinkT / 0.16f) * Mathf.PI));
                if (blinkT > 0.16f) { blinkT = -1f; nextBlink = Random.Range(2.5f, 5f); }
            }
        }
        float talk = talking ? (0.25f + 0.55f * Mathf.PerlinNoise(Time.time * 9f, slot)) : 0f;
        for (int i = 0; i < Shapes.Length; i++)
        {
            float v = manual[i];
            if (i == 0) v = blink;
            if (i == 1) v = Mathf.Max(v, talk);
            smr.SetBlendShapeWeight(i, Mathf.Clamp01(v) * 100f);
        }

        // --- mirada
        float ty = 0f, tp = 0f;
        if (gazeOn && gazeTarget != null)
        {
            Quaternion frame = head.rotation * Quaternion.Inverse(headRestRel);   // = orientacion del modelo con la cabeza girada
            Vector3 mid = (eyeL.position + eyeR.position) * 0.5f;
            Vector3 d = Quaternion.Inverse(frame) * (gazeTarget.position - mid);
            ty = Mathf.Clamp(Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg, -maxYaw, maxYaw);
            tp = Mathf.Clamp(Mathf.Atan2(d.y, new Vector2(d.x, d.z).magnitude) * Mathf.Rad2Deg, -maxPitch, maxPitch);
        }
        float k = 1f - Mathf.Exp(-gazeSpeed * Time.deltaTime);
        yaw = Mathf.Lerp(yaw, ty, k); pitch = Mathf.Lerp(pitch, tp, k);
        Quaternion q = Quaternion.AngleAxis(yaw, Vector3.forward) * Quaternion.AngleAxis(pitch, Vector3.right);
        eyeL.localRotation = restL * q;
        eyeR.localRotation = restR * q;
    }

    static Vector3 FaceOf(string n)
    {
        var g = GameObject.Find(n + "_FacePilot");
        if (g == null) return focus;
        foreach (var t in g.GetComponentsInChildren<Transform>(true)) if (t.name == "head") return t.position + new Vector3(0f, 0.04f, 0f);
        return focus;
    }

    void Set(params (int, float)[] v) { for (int i = 0; i < manual.Length; i++) manual[i] = 0f; foreach (var (i, w) in v) manual[i] = w; }

    void OnGUI()
    {
        if (slot == 0)
        {
            // barra fija abajo: ocultar/mostrar paneles y mirada con el raton
            GUILayout.BeginArea(new Rect(Screen.width - 270, Screen.height - 170, 260, 160), GUI.skin.box);
            panelsVisible = GUILayout.Toggle(panelsVisible, "Mostrar paneles");
            mouseGaze = GUILayout.Toggle(mouseGaze, "Objetivo sigue al raton");
            GUILayout.Label("Zoom " + zoom.ToString("F2"));
            float z = GUILayout.HorizontalSlider(zoom, 0f, 1f);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Lejos")) { focus = new Vector3(0f, 1.3f, 0f); zoom = 0f; z = 0f; }
            if (GUILayout.Button("Cara Gen")) { focus = FaceOf("Gen"); zoom = 1f; z = 1f; }
            if (GUILayout.Button("Cara Gar")) { focus = FaceOf("Gar"); zoom = 1f; z = 1f; }
            GUILayout.EndHorizontal();
            zoom = z;
            if (cam == null) cam = Camera.main;
            if (cam != null)
            {
                float d = Mathf.Lerp(3.6f, 0.55f, zoom), f = Mathf.Lerp(40f, 24f, zoom);
                cam.transform.position = focus + new Vector3(0f, 0f, d);
                cam.transform.rotation = Quaternion.Euler(0f, 180f, 0f);
                cam.fieldOfView = f;
            }
            GUILayout.EndArea();
            if (mouseGaze && gazeTarget != null)
            {
                if (cam == null) cam = Camera.main;
                if (cam != null)
                {
                    Vector2 m = Event.current.mousePosition;
                    Ray r = cam.ScreenPointToRay(new Vector3(m.x, Screen.height - m.y, 0f));
                    Plane p = new Plane(-cam.transform.forward, root.position + new Vector3(0f, 1.55f, 1.2f));
                    if (p.Raycast(r, out float dist)) gazeTarget.position = r.GetPoint(dist);
                }
            }
        }
        if (!panelsVisible) return;
        float w = 210f, x = 10f + slot * (w + 10f);
        GUILayout.BeginArea(new Rect(x, 10, w, Screen.height - 20), GUI.skin.box);
        GUILayout.Label(name);
        scroll = GUILayout.BeginScrollView(scroll);
        GUILayout.Label("Expresion");
        if (GUILayout.Button("Neutral")) Set();
        if (GUILayout.Button("Sonrisa")) Set((2, 0.7f));
        if (GUILayout.Button("Triste/preocupado")) Set((3, 0.6f), (8, 1f));
        if (GUILayout.Button("Sorpresa")) Set((1, 0.8f), (4, 0.4f), (6, 1f));
        talking = GUILayout.Toggle(talking, "Hablando");
        autoBlink = GUILayout.Toggle(autoBlink, "Parpadeo auto");
        gazeOn = GUILayout.Toggle(gazeOn, "Mirar al objetivo (limites +-20/+-12)");
        GUILayout.Label("Blend shapes");
        for (int i = 0; i < Shapes.Length; i++) { GUILayout.Label(Shapes[i] + " " + manual[i].ToString("F2")); manual[i] = GUILayout.HorizontalSlider(manual[i], 0f, 1f); }
        GUILayout.Label("Animacion");
        if (animator != null && animator.runtimeAnimatorController != null)
            foreach (var c in clips) if (GUILayout.Button(c)) animator.CrossFade(c, 0.2f);
        GUILayout.EndScrollView();
        GUILayout.EndArea();
    }
}
