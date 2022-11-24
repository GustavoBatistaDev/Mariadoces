from django.contrib import admin
from .models import Categoria, Produto, Adicional, Opcoes



@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('id','icone', 'nome_produto', 'categoria', 'preco', 'ativo')
    list_editable = ('preco','ativo')
    list_display_links = ('nome_produto', 'icone')


admin.site.register(Categoria)
admin.site.register(Adicional)
admin.site.register(Opcoes)