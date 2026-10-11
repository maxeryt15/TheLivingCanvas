using TheLivingCanvas.Core;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Panel de diálogo: nombre del personaje y una línea cada vez. E / Next avanza; Esc o Close cierran.</summary>
    public class DialogueUI : ModalPanel
    {
        [SerializeField] Text speakerLabel;
        [SerializeField] Text lineLabel;
        [SerializeField] Button nextButton;
        [SerializeField] Text nextLabel;

        string[] lines;
        int index;

        protected override void Awake()
        {
            base.Awake();
            nextButton.onClick.AddListener(Advance);
        }

        public void Open(string speaker, string[] dialogueLines)
        {
            if (!TryOpen()) return;
            speakerLabel.text = speaker;
            lines = dialogueLines;
            index = 0;
            ShowLine();
        }

        protected override void OnInteractPressed()
        {
            if (IsOpen) Advance(); // el handler se dispara también con el panel cerrado
        }

        void Advance()
        {
            if (index >= lines.Length - 1)
            {
                Close();
                return;
            }
            index++;
            ShowLine();
        }

        void ShowLine()
        {
            lineLabel.text = lines[index];
            nextLabel.text = index >= lines.Length - 1 ? "Close" : "Next";
        }
    }
}
