import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_group_name = f'chat_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        if self.user.is_staff:
            await self.channel_layer.group_add(
                'chat_support',
                self.channel_name
            )
        
        await self.accept()
        await self.send_contacts()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        if self.user.is_staff:
            await self.channel_layer.group_discard(
                'chat_support',
                self.channel_name
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'send_message':
            await self.handle_send_message(data)
        elif action == 'get_conversation':
            await self.send_conversation(data)
        elif action == 'get_contacts':
            await self.send_contacts()
    
    async def handle_send_message(self, data):
        from core.models import MessageChat
        from django.contrib.auth.models import User
        
        contenu = data.get('contenu', '').strip()
        destinataire_username = data.get('destinataire', 'admin')
        
        if not contenu:
            return
        
        # Récupérer le destinataire
        destinataire = await database_sync_to_async(self._get_user)(destinataire_username)
        
        # Générer conversation_id
        if destinataire:
            ids = sorted([self.user.id, destinataire.id])
            conversation_id = f"{ids[0]}_{ids[1]}"
        else:
            conversation_id = f"{self.user.id}_admin"
        
        # Créer le message
        message = await database_sync_to_async(MessageChat.objects.create)(
            expediteur=self.user,
            destinataire=destinataire,
            contenu=contenu,
            conversation_id=conversation_id
        )
        
        # Envoyer au destinataire
        if destinataire:
            await self.channel_layer.group_send(
                f'chat_{destinataire.id}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'expediteur': self.user.username,
                        'contenu': contenu,
                        'date_envoi': message.date_envoi.isoformat(),
                    }
                }
            )
        
        await self.send(text_data=json.dumps({
            'type': 'message_sent',
            'message': {
                'id': message.id,
                'contenu': contenu,
                'date_envoi': message.date_envoi.isoformat(),
            }
        }))
        
        if not self.user.is_staff:
            await self.channel_layer.group_send(
                'chat_support',
                {
                    'type': 'support_notification',
                    'message': {
                        'client': self.user.username,
                        'contenu': contenu[:50],
                    }
                }
            )
        
        await self.send_contacts()
    
    async def send_conversation(self, data):
        from core.models import MessageChat
        from django.contrib.auth.models import User
        
        other_username = data.get('other_user')
        if not other_username:
            return
        
        other_user = await database_sync_to_async(self._get_user)(other_username)
        if not other_user:
            await self.send(text_data=json.dumps({
                'type': 'conversation',
                'other_user': other_username,
                'messages': [],
                'error': 'Utilisateur non trouvé'
            }))
            return
        
        # Générer conversation_id
        ids = sorted([self.user.id, other_user.id])
        conversation_id = f"{ids[0]}_{ids[1]}"
        
        # Récupérer les messages
        messages = await database_sync_to_async(self._get_messages)(conversation_id)
        
        result = []
        for m in messages:
            result.append({
                'id': m.id,
                'expediteur': m.expediteur.username,
                'contenu': m.contenu,
                'date_envoi': m.date_envoi.isoformat(),
                'lu': m.lu,
            })
        
        await self.send(text_data=json.dumps({
            'type': 'conversation',
            'other_user': other_username,
            'messages': result
        }))
    
    async def send_contacts(self):
        from core.models import MessageChat
        from django.contrib.auth.models import User
        
        if self.user.is_staff:
            clients = await database_sync_to_async(self._get_clients)()
            
            contacts = []
            for client in clients:
                last_msg = await database_sync_to_async(self._get_last_message)(client)
                unread = await database_sync_to_async(self._get_unread_count)(client)
                
                contacts.append({
                    'username': client.username,
                    'email': client.email,
                    'last_message': last_msg.contenu[:50] if last_msg else '',
                    'unread': unread,
                    'time': last_msg.date_envoi.strftime('%H:%M') if last_msg else '',
                })
        else:
            # Pour les clients : le support
            try:
                admin = await database_sync_to_async(User.objects.get)(username='admin')
                last_msg = await database_sync_to_async(self._get_last_message)(self.user)
                
                contacts = [{
                    'username': 'admin',
                    'email': 'support@boutique.com',
                    'last_message': last_msg.contenu[:50] if last_msg else 'Bonjour, comment puis-je vous aider ?',
                    'unread': 0,
                    'time': last_msg.date_envoi.strftime('%H:%M') if last_msg else '',
                }]
            except User.DoesNotExist:
                contacts = [{
                    'username': 'admin',
                    'email': 'support@boutique.com',
                    'last_message': 'Support disponible',
                    'unread': 0,
                    'time': '',
                }]
        
        await self.send(text_data=json.dumps({
            'type': 'contacts',
            'contacts': contacts
        }))
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))
    
    async def support_notification(self, event):
        if self.user.is_staff:
            await self.send(text_data=json.dumps({
                'type': 'support_notification',
                'data': event['message']
            }))
    
    # ==========================================
    # MÉTHODES SYNC (pour database_sync_to_async)
    # ==========================================
    
    def _get_user(self, username):
        from django.contrib.auth.models import User
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    def _get_messages(self, conversation_id):
        from core.models import MessageChat
        return list(MessageChat.objects.filter(
            conversation_id=conversation_id
        ).order_by('date_envoi'))
    
    def _get_clients(self):
        from django.contrib.auth.models import User
        return list(User.objects.filter(
            messages_envoyes__isnull=False
        ).exclude(is_staff=True).distinct())
    
    def _get_last_message(self, user):
        return user.messages_envoyes.last()
    
    def _get_unread_count(self, user):
        return user.messages_envoyes.filter(lu=False).count()