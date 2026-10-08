namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Cualquier objeto con el que el jugador puede interactuar (lámpara, caballete, cultivo...).
    /// El objeto necesita un Collider (puede ser trigger) en sí mismo o en un hijo.
    /// </summary>
    public interface IInteractable
    {
        /// <summary>Texto de la acción, ej. "Turn on lamp". Puede cambiar según el estado.</summary>
        string Prompt { get; }

        /// <summary>false para ignorarlo temporalmente (ej. un caballete mientras su pintura cobra vida).</summary>
        bool CanInteract { get; }

        void Interact(PlayerInteractor interactor);
    }
}
