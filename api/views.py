import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .interpreter.interpreter import CompilerEngine

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def execute_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            
            # Run interpreter
            engine = CompilerEngine()
            result = engine.execute(code)
            
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
