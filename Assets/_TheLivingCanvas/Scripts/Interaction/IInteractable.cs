namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Cualquier objeto con el que el jugador puede interactuar (lámpara, caballete, cultivo...).
    /// El objeto necesita un Collider (puede ser trigger) en sí mismo o en un hijo.
    /// </summary>
    public interface IInteractable
    {
        /// <summary>Texto de la acción, ej. "Encender lámpara". Puede cambiar según el estado.</summary>
        string Prompt { get; }

        void Interact(PlayerInteractor interactor);
    }
}
