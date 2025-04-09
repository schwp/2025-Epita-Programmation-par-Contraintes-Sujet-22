# Process Allocation Output Generator

This tool generates YAML output files showing the allocation of processes to servers, based on the solution from the main.py program.

## Usage

Run the script with the preset name as an argument:

```bash
python generate_output.py tiny-x
```

This will:
1. Run the main.py script using the specified preset
2. Parse the process allocation results
3. Generate a YAML file showing which processes are assigned to each server
4. Save the file as `output-processes-dispatch-{preset_name}.yml`

### Command Line Options

- `preset`: (Required) The name of the preset folder to use (e.g., tiny-x)
- `--output-dir`: (Optional) Directory where to save the output file. Defaults to current directory.

Example:
```bash
python generate_output.py tiny-x --output-dir ./output
```

## Output Format

The generated YAML file has the following structure:

```yaml
servers:
  - name: server_name1
    processes:
      - name: process_name1
        replica: 1
        location: location_name
      - name: process_name2
        replica: 2
        location: location_name
  - name: server_name2
    processes:
      - name: process_name3
        replica: 1
        location: location_name
```

This format makes it easy to see which processes are assigned to each server, including their replica numbers and locations.

## Integration with Deployment Systems

This output file can be used to feed into deployment systems, container orchestrators, or configuration management tools to automatically deploy the services according to the calculated optimal allocation.
