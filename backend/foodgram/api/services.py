from django.http import HttpResponse


def get_shoping_cart_file(shopping_cart):
    response = HttpResponse(content_type='text/plain')
    response[
        'Content-Disposition'
    ] = 'attachment; filename="shopping_cart.txt"'
    for ingredient in shopping_cart:
        name = ingredient['ingredient__name']
        amount = ingredient['amount']
        unit = ingredient['ingredient__measurement_unit']
        line = f"{name} — {amount} {unit}\n"
        response.write(line)
    return response
