using System.Collections;
using TheLivingCanvas.Audio;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Growth;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Save;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Tutorial
{
    /// <summary>
    /// Tutorial como cadena de objetivos en una esquina del HUD. Solo escucha el evento del paso actual;
    /// al cumplirlo se marca en verde un momento y pasa al siguiente. El paso se guarda en la partida.
    /// </summary>
    public class TutorialObjectives : MonoBehaviour, ISaveable
    {
        // El orden coincide con el índice guardado (y con Subscribe).
        static readonly string[] Steps =
        {
            "Paint a sunflower at the easel",
            "Take the painting from the easel",
            "Open your bag (I) and place the painting on the ground",
            "Wait for it to grow, then harvest it",
            "Sell your harvest at the crate",
            "Visit the shop and buy something"
        };

        const string CompleteText = "Tutorial complete!";

        [SerializeField] PaintingFinisher finisher;
        [SerializeField] PaintingPlacer placer;
        [SerializeField] PlayerInventory inventory;
        [SerializeField] Wallet wallet;
        [SerializeField] GameObject panel;
        [SerializeField] Text label;
        [SerializeField] Color normalColor = new(1f, 0.95f, 0.82f);
        [SerializeField] Color doneColor = new(0.55f, 0.85f, 0.4f);
        [SerializeField] float tickSeconds = 1f;
        [SerializeField] float completeSeconds = 4f;

        int step;
        Coroutine routine;

        void OnEnable()
        {
            Subscribe();
            Refresh();
        }

        void OnDisable()
        {
            Unsubscribe();
            routine = null; // Unity detiene las corrutinas al desactivar
        }

        void Subscribe()
        {
            switch (step)
            {
                case 0: finisher.Finished += Advance; break;
                case 1: case 3: inventory.ItemAdded += OnItemAdded; break;
                case 2: placer.Placed += Advance; break;
                case 4: case 5: wallet.Changed += OnCoinsChanged; break;
            }
        }

        void Unsubscribe()
        {
            finisher.Finished -= Advance;
            inventory.ItemAdded -= OnItemAdded;
            placer.Placed -= Advance;
            wallet.Changed -= OnCoinsChanged;
        }

        void OnItemAdded(InventoryItem item)
        {
            bool expected = step == 1 ? item is PaintingItem && item is not SeedItem : item is CropItem;
            if (expected) Advance();
        }

        void OnCoinsChanged(int total, int delta)
        {
            if (step == 4 ? delta > 0 : delta < 0) Advance();
        }

        void Advance()
        {
            Unsubscribe();
            step++;
            Subscribe(); // ya escucha el paso siguiente: el verde de TickThenNext es solo visual
            SfxPlayer.Play(Sfx.UiOpen);
            if (routine != null) StopCoroutine(routine);
            routine = StartCoroutine(TickThenNext());
        }

        IEnumerator TickThenNext()
        {
            label.color = doneColor; // el texto del paso cumplido se queda en verde un momento
            yield return new WaitForSecondsRealtime(tickSeconds);
            routine = null;
            if (step < Steps.Length)
            {
                Refresh();
                yield break;
            }
            label.text = CompleteText;
            yield return new WaitForSecondsRealtime(completeSeconds);
            panel.SetActive(false);
        }

        void Refresh()
        {
            label.color = normalColor;
            panel.SetActive(step < Steps.Length);
            if (step < Steps.Length) label.text = Steps[step];
        }

        public void WriteSave(SaveData data) => data.tutorialStep = step;

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            if (routine != null) StopCoroutine(routine);
            routine = null;
            Unsubscribe();
            step = Mathf.Clamp(data.tutorialStep, 0, Steps.Length);
            Subscribe();
            Refresh(); // sin sonido ni verde: solo muestra el paso guardado
        }
    }
}
