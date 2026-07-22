from django.shortcuts import render, redirect # Asegúrate de importar 'redirect'
from django.contrib.auth.forms import UserCreationForm # O el formulario que uses

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save() 
            
            return redirect('tienda_home') 
    else:
        form = UserCreationForm()
        
    return render(request, 'usuarios/registro.html', {'form': form})