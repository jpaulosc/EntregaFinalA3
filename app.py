from library import console, _

class app:

  COMMAND_CODE = None
  INPUT_PREFIX = ''
        
  def command_code(self) -> bool :
    codigo = input(f"{self.INPUT_PREFIX}")
    if codigo.isdigit():
      self.COMMAND_CODE = int(codigo)
      return True
    elif not codigo:
      return False
    else:
      console.print_alerta(_("invalid.input"))
    return False