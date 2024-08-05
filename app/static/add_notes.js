document.addEventListener("DOMContentLoaded", function () {
    const noteTitle = document.getElementById("note-title");
    const noteContent = document.getElementById("note-content");
    const saveButton = document.getElementById("save-button");
    const savedNotes = document.getElementById("saved-notes");

    let editNoteIndex = -1; // Track the index of the note being edited

    function fetchAndDisplayNotes() {
        // Fetch and display notes from the API
        fetch("/api/notes")
            .then((response) => response.json())
            .then((data) => {
                savedNotes.innerHTML = ""; // Clear the saved notes section
    
                // Iterate through the notes and display them
                data.forEach((note, index) => {
                    // Split the note into title and content
                    const [title, content] = note.split(": ");
    
                    const noteDiv = document.createElement("div");
                    noteDiv.classList.add("saved-note", "alert", "alert-info");
                    noteDiv.setAttribute("data-note-text", note);
    
                    // Create separate elements for title and content
                    const titleElement = document.createElement("strong");
                    titleElement.textContent = title;
                    titleElement.classList.add("title-element");
    
                    const contentElement = document.createElement("div");
                    contentElement.innerHTML = content; // Use innerHTML to include HTML content
    
                    noteDiv.appendChild(titleElement);
    
                    // Create Edit and Delete buttons
                    const editButton = document.createElement("span");
                    const editIcon = document.createElement("i");
                    editIcon.classList.add("fas", "fa-edit", "icon"); // Add Font Awesome edit icon classes
                    editButton.appendChild(editIcon);
                    editButton.addEventListener("click", function () {
                        editNoteIndex = index;
                        const [editTitle, editContent] = note.split(": ");
                        noteTitle.value = editTitle;
                        noteContent.value = editContent;
                        saveButton.textContent = "Update"; // Change the button text to "Update"
                    });
    
                    // Create a close icon
                    const deleteButton = document.createElement("span");
                    const deleteIcon = document.createElement("i");
                    deleteIcon.classList.add("fas", "fa-trash-alt", "icon"); // Add Font Awesome trash icon classes
                    deleteButton.appendChild(deleteIcon);
                    deleteButton.addEventListener("click", function () {
                        const noteText = noteDiv.getAttribute("data-note-text");
                        deleteNote(noteText);
                    });
    
                    // Create a container div for the icons and set its style for positioning
                    const iconsContainer = document.createElement("span");
                    iconsContainer.classList.add("icons-container");
    
                    // Append icons to the icons container
                    iconsContainer.appendChild(editButton);
                    iconsContainer.appendChild(deleteButton);
    
                    // Append the icons container to the noteDiv
                    noteDiv.appendChild(iconsContainer);
                    noteDiv.appendChild(contentElement);

                    savedNotes.appendChild(noteDiv);
                });
            });
    }
    
    

    function saveNote() {
        const title = noteTitle.value.trim();
        const content = noteContent.value.trim();
        if (title !== "" && content !== "") {
            const newNote = `${title}: ${content}`;
            if (editNoteIndex !== -1) {
                // If in edit mode, update the existing note
                fetch("/api/notes", {
                    method: "PUT", // Use PUT method to update the note
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ index: editNoteIndex, text: newNote }),
                })
                    .then(() => {
                        editNoteIndex = -1; // Exit edit mode
                        saveButton.textContent = "Save Notes"; // Change the button text back to "Save"
                        // After saving the edited note, fetch and display the updated notes
                        fetchAndDisplayNotes();
                        noteTitle.value = ""; // Clear the title input
                        noteContent.value = ""; // Clear the content textarea
                    });
            } else {
                // If not in edit mode, add a new note
                fetch("/api/notes", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(newNote),
                })
                    .then(() => {
                        // After saving the note, fetch and display the updated notes
                        fetchAndDisplayNotes();
                        noteTitle.value = ""; // Clear the title input
                        noteContent.value = ""; // Clear the content textarea
                    });
            }
        }
    }

    function deleteNote(text) {
        if (confirm("Are you sure you want to delete this note?")) {
            fetch("/api/notes", {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ text }),
            })
                .then(() => {
                    // After deleting a note, fetch and display the updated notes
                    fetchAndDisplayNotes();
                });
        }
    }

    // Event listener for the Save button
    saveButton.addEventListener("click", saveNote);

    // Fetch and display notes when the page loads
    fetchAndDisplayNotes();
});