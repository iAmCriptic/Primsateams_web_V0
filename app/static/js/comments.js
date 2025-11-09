/**
 * Kommentar-System JavaScript
 * Verwaltet Kommentare für Dateien, Wiki-Seiten und Canvas
 */

class CommentSystem {
    constructor(contentType, contentId, containerId) {
        this.contentType = contentType;
        this.contentId = contentId;
        this.containerId = containerId;
        this.currentUserId = null;
        this.mentionCache = {};
        this.init();
    }
    
    init() {
        // Hole aktuelle Benutzer-ID (wird vom Template gesetzt)
        const userElement = document.getElementById('current-user-id');
        if (userElement && userElement.dataset.userId) {
            this.currentUserId = parseInt(userElement.dataset.userId);
        }
        
        this.loadComments();
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        const container = document.getElementById(this.containerId);
        if (!container) return;
        
        // Submit-Button für neuen Kommentar
        const submitBtn = container.querySelector('.comment-submit-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.createComment());
        }
        
        // Enter-Taste für Kommentar-Erstellung (Ctrl+Enter)
        const textarea = container.querySelector('.comment-textarea');
        if (textarea) {
            textarea.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    this.createComment();
                }
            });
            
            // @-Mention Autovervollständigung
            textarea.addEventListener('input', (e) => this.handleMentionInput(e));
            textarea.addEventListener('keydown', (e) => this.handleMentionKeydown(e));
        }
    }
    
    async loadComments() {
        const container = document.getElementById(this.containerId);
        if (!container) return;
        
        const commentsList = container.querySelector('.comments-list');
        if (!commentsList) return;
        
        commentsList.innerHTML = '<div class="comment-loading">Lade Kommentare...</div>';
        
        try {
            const response = await fetch(`/api/comments/${this.contentType}/${this.contentId}`);
            const data = await response.json();
            
            if (data.comments) {
                this.renderComments(data.comments, commentsList);
                this.updateCommentCount(data.comments.length);
            } else {
                commentsList.innerHTML = '<div class="comment-empty">Noch keine Kommentare</div>';
            }
        } catch (error) {
            console.error('Fehler beim Laden der Kommentare:', error);
            commentsList.innerHTML = '<div class="comment-empty">Fehler beim Laden der Kommentare</div>';
        }
    }
    
    renderComments(comments, container) {
        if (comments.length === 0) {
            container.innerHTML = '<div class="comment-empty">Noch keine Kommentare</div>';
            return;
        }
        
        container.innerHTML = '';
        comments.forEach(comment => {
            const commentElement = this.createCommentElement(comment);
            container.appendChild(commentElement);
        });
    }
    
    createCommentElement(comment) {
        const li = document.createElement('li');
        li.className = 'comment-item';
        li.dataset.commentId = comment.id;
        
        const avatar = this.getAvatar(comment.author);
        const formattedDate = this.formatDate(comment.created_at);
        const formattedContent = this.formatContent(comment.content);
        
        li.innerHTML = `
            <div class="comment-header">
                <div class="comment-avatar">${avatar}</div>
                <div>
                    <span class="comment-author">${this.escapeHtml(comment.author.name)}</span>
                    <span class="comment-date">${formattedDate}</span>
                </div>
            </div>
            <div class="comment-content">${formattedContent}</div>
            <div class="comment-actions">
                <button class="comment-action-btn reply-btn" data-comment-id="${comment.id}">
                    <i class="bi bi-reply"></i> Antworten
                </button>
                ${comment.author.id === this.currentUserId ? `
                    <button class="comment-action-btn edit-btn" data-comment-id="${comment.id}">
                        <i class="bi bi-pencil"></i> Bearbeiten
                    </button>
                    <button class="comment-action-btn danger delete-btn" data-comment-id="${comment.id}">
                        <i class="bi bi-trash"></i> Löschen
                    </button>
                ` : ''}
            </div>
            ${comment.replies && comment.replies.length > 0 ? `
                <div class="comment-replies">
                    ${comment.replies.map(reply => this.createCommentElement(reply).outerHTML).join('')}
                </div>
            ` : ''}
        `;
        
        // Event Listener für Buttons
        const replyBtn = li.querySelector('.reply-btn');
        if (replyBtn) {
            replyBtn.addEventListener('click', () => this.showReplyForm(comment.id));
        }
        
        const editBtn = li.querySelector('.edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => this.showEditForm(comment.id));
        }
        
        const deleteBtn = li.querySelector('.delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.deleteComment(comment.id));
        }
        
        return li;
    }
    
    getAvatar(author) {
        if (author.profile_picture) {
            return `<img src="${this.escapeHtml(author.profile_picture)}" alt="${this.escapeHtml(author.name)}">`;
        }
        const initials = author.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        return initials;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'gerade eben';
        if (diffMins < 60) return `vor ${diffMins} Min`;
        if (diffHours < 24) return `vor ${diffHours} Std`;
        if (diffDays < 7) return `vor ${diffDays} Tag${diffDays > 1 ? 'en' : ''}`;
        
        return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) + 
               ' ' + date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
    }
    
    formatContent(content) {
        // Ersetze @-Mentions mit Links
        const mentionRegex = /@(\w+(?:\s+\w+)?)/g;
        return this.escapeHtml(content).replace(mentionRegex, '<span class="mention">@$1</span>');
    }
    
    async createComment(parentId = null) {
        const container = document.getElementById(this.containerId);
        const textarea = parentId 
            ? container.querySelector(`.comment-reply-form[data-parent-id="${parentId}"] .comment-textarea`)
            : container.querySelector('.comment-textarea');
        
        if (!textarea) return;
        
        const content = textarea.value.trim();
        if (!content) {
            alert('Bitte geben Sie einen Kommentar ein.');
            return;
        }
        
        const submitBtn = parentId
            ? container.querySelector(`.comment-reply-form[data-parent-id="${parentId}"] .comment-submit-btn`)
            : container.querySelector('.comment-submit-btn');
        
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Wird gesendet...';
        }
        
        try {
            const response = await fetch(`/api/comments/${this.contentType}/${this.contentId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    parent_id: parentId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                textarea.value = '';
                this.hideMentionSuggestions();
                this.loadComments();
                
                // Verstecke Reply-Form falls vorhanden
                if (parentId) {
                    const replyForm = container.querySelector(`.comment-reply-form[data-parent-id="${parentId}"]`);
                    if (replyForm) {
                        replyForm.remove();
                    }
                }
            } else {
                alert('Fehler beim Erstellen des Kommentars: ' + (data.error || 'Unbekannter Fehler'));
            }
        } catch (error) {
            console.error('Fehler beim Erstellen des Kommentars:', error);
            alert('Fehler beim Erstellen des Kommentars.');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Kommentar senden';
            }
        }
    }
    
    showReplyForm(parentId) {
        const container = document.getElementById(this.containerId);
        
        // Entferne vorhandene Reply-Forms
        container.querySelectorAll('.comment-reply-form').forEach(form => form.remove());
        
        const parentComment = container.querySelector(`.comment-item[data-comment-id="${parentId}"]`);
        if (!parentComment) return;
        
        const replyForm = document.createElement('div');
        replyForm.className = 'comment-reply-form';
        replyForm.dataset.parentId = parentId;
        replyForm.innerHTML = `
            <div class="comment-input-wrapper">
                <textarea class="comment-textarea" placeholder="Antwort schreiben..."></textarea>
                <div class="comment-mention-suggestions"></div>
            </div>
            <div class="comment-form-actions">
                <button class="btn btn-secondary btn-sm" onclick="this.closest('.comment-reply-form').remove()">
                    Abbrechen
                </button>
                <button class="btn btn-primary btn-sm comment-submit-btn" onclick="window.commentSystem.createComment(${parentId})">
                    Antworten
                </button>
            </div>
        `;
        
        parentComment.appendChild(replyForm);
        
        // Event Listener für Textarea
        const textarea = replyForm.querySelector('.comment-textarea');
        if (textarea) {
            textarea.focus();
            textarea.addEventListener('input', (e) => this.handleMentionInput(e));
            textarea.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    this.createComment(parentId);
                } else {
                    this.handleMentionKeydown(e);
                }
            });
        }
    }
    
    async showEditForm(commentId) {
        const container = document.getElementById(this.containerId);
        const commentItem = container.querySelector(`.comment-item[data-comment-id="${commentId}"]`);
        if (!commentItem) return;
        
        const contentDiv = commentItem.querySelector('.comment-content');
        const currentContent = contentDiv.textContent;
        
        const editForm = document.createElement('div');
        editForm.className = 'comment-edit-form';
        editForm.innerHTML = `
            <div class="comment-input-wrapper">
                <textarea class="comment-textarea">${this.escapeHtml(currentContent)}</textarea>
            </div>
            <div class="comment-form-actions">
                <button class="btn btn-secondary btn-sm" onclick="this.closest('.comment-edit-form').remove(); this.closest('.comment-item').querySelector('.comment-content').style.display = 'block'">
                    Abbrechen
                </button>
                <button class="btn btn-primary btn-sm" onclick="window.commentSystem.updateComment(${commentId})">
                    Speichern
                </button>
            </div>
        `;
        
        contentDiv.style.display = 'none';
        contentDiv.parentNode.insertBefore(editForm, contentDiv.nextSibling);
        
        const textarea = editForm.querySelector('.comment-textarea');
        if (textarea) {
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }
    }
    
    async updateComment(commentId) {
        const container = document.getElementById(this.containerId);
        const commentItem = container.querySelector(`.comment-item[data-comment-id="${commentId}"]`);
        if (!commentItem) return;
        
        const editForm = commentItem.querySelector('.comment-edit-form');
        const textarea = editForm.querySelector('.comment-textarea');
        const content = textarea.value.trim();
        
        if (!content) {
            alert('Kommentar-Inhalt darf nicht leer sein.');
            return;
        }
        
        try {
            const response = await fetch(`/api/comments/${commentId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadComments();
            } else {
                alert('Fehler beim Aktualisieren des Kommentars: ' + (data.error || 'Unbekannter Fehler'));
            }
        } catch (error) {
            console.error('Fehler beim Aktualisieren des Kommentars:', error);
            alert('Fehler beim Aktualisieren des Kommentars.');
        }
    }
    
    async deleteComment(commentId) {
        if (!confirm('Möchten Sie diesen Kommentar wirklich löschen?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/comments/${commentId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.loadComments();
            } else {
                alert('Fehler beim Löschen des Kommentars: ' + (data.error || 'Unbekannter Fehler'));
            }
        } catch (error) {
            console.error('Fehler beim Löschen des Kommentars:', error);
            alert('Fehler beim Löschen des Kommentars.');
        }
    }
    
    async handleMentionInput(e) {
        const textarea = e.target;
        const cursorPos = textarea.selectionStart;
        const textBeforeCursor = textarea.value.substring(0, cursorPos);
        const lastAtIndex = textBeforeCursor.lastIndexOf('@');
        
        if (lastAtIndex === -1 || lastAtIndex === cursorPos - 1) {
            this.hideMentionSuggestions();
            return;
        }
        
        const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
        if (/\s/.test(textAfterAt)) {
            this.hideMentionSuggestions();
            return;
        }
        
        if (textAfterAt.length >= 2) {
            await this.showMentionSuggestions(textarea, textAfterAt, lastAtIndex);
        } else {
            this.hideMentionSuggestions();
        }
    }
    
    async showMentionSuggestions(textarea, query, atIndex) {
        const container = textarea.closest('.comment-input-wrapper');
        if (!container) return;
        
        let suggestionsDiv = container.querySelector('.comment-mention-suggestions');
        if (!suggestionsDiv) {
            suggestionsDiv = document.createElement('div');
            suggestionsDiv.className = 'comment-mention-suggestions';
            container.appendChild(suggestionsDiv);
        }
        
        // Cache für Mentions
        if (!this.mentionCache[query]) {
            try {
                const response = await fetch(`/api/comments/users/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                this.mentionCache[query] = data.users || [];
            } catch (error) {
                console.error('Fehler beim Laden der Benutzer:', error);
                this.mentionCache[query] = [];
            }
        }
        
        const users = this.mentionCache[query];
        
        if (users.length === 0) {
            suggestionsDiv.innerHTML = '<div class="comment-mention-item">Keine Benutzer gefunden</div>';
        } else {
            suggestionsDiv.innerHTML = users.map((user, index) => `
                <div class="comment-mention-item ${index === 0 ? 'selected' : ''}" 
                     data-user-name="${this.escapeHtml(user.mention)}"
                     onclick="window.commentSystem.insertMention('${this.escapeHtml(user.mention)}', ${atIndex})">
                    <div class="mention-name">${this.escapeHtml(user.name)}</div>
                    <div class="mention-email">${this.escapeHtml(user.email)}</div>
                </div>
            `).join('');
        }
        
        suggestionsDiv.classList.add('active');
        this.selectedMentionIndex = 0;
        this.mentionAtPosition = atIndex;
    }
    
    hideMentionSuggestions() {
        document.querySelectorAll('.comment-mention-suggestions').forEach(div => {
            div.classList.remove('active');
        });
    }
    
    insertMention(mentionText, atIndex) {
        const container = document.getElementById(this.containerId);
        const textarea = container.querySelector('.comment-textarea:focus') || 
                        container.querySelector('.comment-textarea');
        if (!textarea) return;
        
        const textBefore = textarea.value.substring(0, atIndex);
        const textAfter = textarea.value.substring(textarea.selectionStart);
        const newText = textBefore + mentionText + ' ' + textAfter;
        
        textarea.value = newText;
        const newCursorPos = atIndex + mentionText.length + 1;
        textarea.setSelectionRange(newCursorPos, newCursorPos);
        textarea.focus();
        
        this.hideMentionSuggestions();
    }
    
    handleMentionKeydown(e) {
        const suggestionsDiv = document.querySelector('.comment-mention-suggestions.active');
        if (!suggestionsDiv) return;
        
        const items = suggestionsDiv.querySelectorAll('.comment-mention-item');
        if (items.length === 0) return;
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.selectedMentionIndex = Math.min(this.selectedMentionIndex + 1, items.length - 1);
            this.updateMentionSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.selectedMentionIndex = Math.max(this.selectedMentionIndex - 1, 0);
            this.updateMentionSelection(items);
        } else if (e.key === 'Enter' && !e.ctrlKey) {
            e.preventDefault();
            const selectedItem = items[this.selectedMentionIndex];
            if (selectedItem) {
                const mentionText = selectedItem.dataset.userName;
                this.insertMention(mentionText, this.mentionAtPosition);
            }
        } else if (e.key === 'Escape') {
            this.hideMentionSuggestions();
        }
    }
    
    updateMentionSelection(items) {
        items.forEach((item, index) => {
            if (index === this.selectedMentionIndex) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });
    }
    
    updateCommentCount(count) {
        const container = document.getElementById(this.containerId);
        const countElement = container.querySelector('.comment-count');
        if (countElement) {
            countElement.textContent = `${count} Kommentar${count !== 1 ? 'e' : ''}`;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Globale Instanz für Zugriff von onclick-Handlern
window.commentSystem = null;

